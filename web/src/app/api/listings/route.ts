import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth-helpers";

const ListingSchema = z.object({
  titre: z.string().min(3).max(200),
  description: z.string().max(5000).optional(),
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

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON" }, { status: 400 });
  }
  const parsed = ListingSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "validation", issues: parsed.error.flatten() }, { status: 400 });
  }

  const { images, prix, ...rest } = parsed.data;
  const listing = await prisma.listing.create({
    data: {
      ...rest,
      prix: prix ?? null,
      images: images.join(" | "),
      isUserCreated: true,
      ownerId: Number(session.user.id),
      source: "user",
      datePublication: new Date().toISOString(),
    },
    select: { id: true },
  });

  return NextResponse.json({ id: listing.id });
}
