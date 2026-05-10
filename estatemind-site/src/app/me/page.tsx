import { getServerSession } from "next-auth/next";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { DashboardClient } from "./dashboard-client";

export default async function MePage() {
  const session = await getServerSession(authOptions);
  if (!session?.user) redirect("/signin");

  const userId = parseInt(session.user.id as string, 10);

  const [user, myListings, rawFavorites] = await Promise.all([
    prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, email: true, name: true, role: true, createdAt: true },
    }),
    prisma.listing.findMany({
      where: { ownerId: userId },
      orderBy: { createdAt: "desc" },
      select: { id: true, titre: true, prix: true, gouvernerat: true, ville: true, type: true, contrat: true, surface: true, pieces: true, images: true, createdAt: true },
    }),
    prisma.favorite.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      select: {
        listing: {
          select: { id: true, titre: true, prix: true, gouvernerat: true, ville: true, type: true, contrat: true, surface: true, pieces: true, images: true },
        },
      },
    }),
  ]);

  return (
    <DashboardClient
      user={{ id: user?.id ?? userId, email: user?.email ?? session.user.email ?? "", name: user?.name ?? null, role: user?.role ?? "buyer", createdAt: user?.createdAt?.toISOString() ?? new Date().toISOString() }}
      myListings={myListings.map(l => ({ ...l, createdAt: l.createdAt.toISOString() }))}
      favorites={rawFavorites.map(f => f.listing)}
    />
  );
}
