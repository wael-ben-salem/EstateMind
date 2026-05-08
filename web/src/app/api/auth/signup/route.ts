import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  let body: { email?: string; password?: string; name?: string; role?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const email = body.email?.toLowerCase().trim();
  const password = body.password ?? "";
  const name = body.name?.trim() || null;
  const role = body.role === "seller" ? "seller" : "buyer";

  if (!email || !email.includes("@") || password.length < 6) {
    return NextResponse.json(
      { error: "Email valide + mot de passe ≥ 6 caractères requis" },
      { status: 400 }
    );
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return NextResponse.json({ error: "Cet email est déjà inscrit" }, { status: 409 });
  }

  await prisma.user.create({
    data: { email, name, role, passwordHash: await bcrypt.hash(password, 10) },
  });

  return NextResponse.json({ ok: true });
}
