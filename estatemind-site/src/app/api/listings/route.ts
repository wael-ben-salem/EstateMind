import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { z } from "zod";

const schema = z.object({
  titre:       z.string().min(3).max(200),
  type:        z.string().optional(),
  contrat:     z.string().optional(),
  gouvernerat: z.string().optional(),
  ville:       z.string().optional(),
  adresse:     z.string().optional(),
  surface:     z.number().positive().optional(),
  pieces:      z.number().int().positive().optional(),
  prix:        z.number().positive().optional(),
  description: z.string().optional(),
  images:      z.string().optional(),
  tel:         z.string().optional(),
  hasAscenseur:     z.boolean().optional(),
  hasBalcon:        z.boolean().optional(),
  hasClimatisation: z.boolean().optional(),
  hasGarage:        z.boolean().optional(),
  hasJardin:        z.boolean().optional(),
  hasParking:       z.boolean().optional(),
  hasPiscine:       z.boolean().optional(),
  hasTerrasse:      z.boolean().optional(),
});

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) return NextResponse.json({ error: "Non authentifié." }, { status: 401 });

  try {
    const body = await req.json();
    const data = schema.parse(body);
    const listing = await prisma.listing.create({
      data: { ...data, ownerId: parseInt(session.user.id as string, 10), isUserCreated: true },
    });
    return NextResponse.json({ id: listing.id }, { status: 201 });
  } catch (err) {
    if (err instanceof z.ZodError) return NextResponse.json({ error: "Données invalides.", details: err.issues }, { status: 400 });
    return NextResponse.json({ error: "Erreur serveur." }, { status: 500 });
  }
}
