import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth-helpers";

const PatchSchema = z.object({
  titre: z.string().min(3).max(200),
  description: z.string().max(5000).optional().nullable(),
  prix: z.number().positive().optional().nullable(),
  contrat: z.enum(["vente", "location"]),
  type: z.string().min(1).max(60),
  gouvernerat: z.string().min(1).max(60),
  ville: z.string().max(60).optional().nullable(),
  adresse: z.string().max(200).optional().nullable(),
  surface: z.number().positive().optional().nullable(),
  pieces: z.number().int().nonnegative().optional().nullable(),
  etage: z.number().int().optional().nullable(),
  tel: z.string().max(40).optional().nullable(),
  hasAscenseur: z.boolean().optional(),
  hasBalcon: z.boolean().optional(),
  hasChaffage: z.boolean().optional(),
  hasClimatisation: z.boolean().optional(),
  hasGarage: z.boolean().optional(),
  hasGardien: z.boolean().optional(),
  hasJardin: z.boolean().optional(),
  hasParking: z.boolean().optional(),
  hasPiscine: z.boolean().optional(),
  hasTerrasse: z.boolean().optional(),
  images: z.array(z.string().min(1)).min(1).max(20),
});

export async function PATCH(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const { id } = await ctx.params;
  const numId = Number(id);
  if (!Number.isInteger(numId)) {
    return NextResponse.json({ error: "invalid id" }, { status: 400 });
  }
  const listing = await prisma.listing.findUnique({ where: { id: numId } });
  if (!listing) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (listing.ownerId !== Number(session.user.id)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  let body: unknown;
  try { body = await req.json(); } catch {
    return NextResponse.json({ error: "invalid JSON" }, { status: 400 });
  }
  const parsed = PatchSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "validation", issues: parsed.error.flatten() }, { status: 400 });
  }

  const { images, prix, ...rest } = parsed.data;
  await prisma.listing.update({
    where: { id: numId },
    data: { ...rest, prix: prix ?? null, images: images.join(" | ") },
  });

  return NextResponse.json({ ok: true });
}

export async function DELETE(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const { id } = await ctx.params;
  const numId = Number(id);
  if (!Number.isInteger(numId)) {
    return NextResponse.json({ error: "invalid id" }, { status: 400 });
  }
  const listing = await prisma.listing.findUnique({ where: { id: numId } });
  if (!listing) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  if (listing.ownerId !== Number(session.user.id)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }
  await prisma.listing.delete({ where: { id: numId } });
  return NextResponse.json({ ok: true });
}
