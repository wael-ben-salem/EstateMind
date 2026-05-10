import { prisma } from "@/lib/prisma";
import { HomeClient } from "./home-client";

export default async function HomePage() {
  const [featured, cities, total] = await Promise.all([
    prisma.listing.findMany({
      where: { prix: { gt: 100 }, images: { not: null } },
      orderBy: { createdAt: "desc" },
      take: 6,
      select: { id: true, titre: true, prix: true, gouvernerat: true, ville: true, type: true, contrat: true, surface: true, pieces: true, images: true },
    }),
    prisma.listing.groupBy({
      by: ["gouvernerat"],
      where: { gouvernerat: { not: null } },
      _count: { id: true },
      orderBy: { _count: { id: "desc" } },
      take: 4,
    }),
    prisma.listing.count(),
  ]);

  return <HomeClient featured={featured} cities={cities} total={total} />;
}
