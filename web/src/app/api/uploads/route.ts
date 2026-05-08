import { NextResponse } from "next/server";
import { mkdir, writeFile } from "fs/promises";
import { join, extname } from "path";
import { randomUUID } from "crypto";
import { auth } from "@/lib/auth-helpers";

const UPLOADS_DIR = join(process.cwd(), "public", "uploads");
const ALLOWED_EXT = new Set([".jpg", ".jpeg", ".png", ".webp", ".avif"]);
const MAX_BYTES = 10 * 1024 * 1024; // 10 MB per file

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const form = await req.formData();
  const files = form.getAll("files").filter((x): x is File => x instanceof File);
  if (files.length === 0) {
    return NextResponse.json({ error: "no files" }, { status: 400 });
  }

  const folderId = randomUUID();
  const dir = join(UPLOADS_DIR, folderId);
  await mkdir(dir, { recursive: true });

  const urls: string[] = [];
  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    const ext = extname(f.name).toLowerCase();
    if (!ALLOWED_EXT.has(ext)) {
      return NextResponse.json({ error: `extension non supportée : ${ext}` }, { status: 400 });
    }
    if (f.size > MAX_BYTES) {
      return NextResponse.json({ error: `fichier trop volumineux : ${f.name}` }, { status: 400 });
    }
    const safeName = `${i + 1}${ext}`;
    const buf = Buffer.from(await f.arrayBuffer());
    await writeFile(join(dir, safeName), buf);
    urls.push(`/uploads/${folderId}/${safeName}`);
  }

  return NextResponse.json({ folderId, urls });
}
