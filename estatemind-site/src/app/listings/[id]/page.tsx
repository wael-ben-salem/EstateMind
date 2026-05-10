import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { ListingContent } from "./listing-content";

export default async function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const listingId = parseInt(id, 10);
  if (isNaN(listingId)) notFound();

  const l = await prisma.listing.findUnique({
    where: { id: listingId },
    select: {
      id: true, titre: true, prix: true, prixM2: true, gouvernerat: true, ville: true,
      delegation: true, adresse: true, type: true, contrat: true, surface: true, pieces: true,
      images: true, description: true, descClean: true, tel: true, source: true, url: true,
      pubYear: true, hautStanding: true, hasAscenseur: true, hasBalcon: true,
      hasClimatisation: true, hasGarage: true, hasGardien: true, hasJardin: true,
      hasParking: true, hasPiscine: true, hasTerrasse: true, hasChaffage: true,
    },
  });
  if (!l) notFound();

  return <ListingContent l={l} />;
}
