import Link from "next/link";
import { Heart } from "lucide-react";
import { notFound, redirect } from "next/navigation";
import { isLocale, getDict } from "@/i18n/dictionaries";
import { auth } from "@/lib/auth-helpers";
import { prisma } from "@/lib/prisma";
import { ListingCard } from "@/components/listings/listing-card";
import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";

export default async function FavoritesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const session = await auth();
  if (!session?.user) {
    redirect(`/${locale}/signin?callbackUrl=${encodeURIComponent(`/${locale}/favorites`)}`);
  }
  const dict = await getDict(locale);
  const userId = Number(session.user.id);

  const favorites = await prisma.favorite.findMany({
    where: { userId },
    include: { listing: true },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center gap-2">
        <Heart className="size-5 text-destructive" />
        <h1 className="text-2xl font-semibold tracking-tight">Mes favoris</h1>
        <span className="text-sm text-muted-foreground">({favorites.length})</span>
      </div>

      {favorites.length === 0 ? (
        <Card className="p-10 text-center text-sm text-muted-foreground">
          <p className="mb-3">Vous n&apos;avez pas encore enregistré de favoris.</p>
          <Link href={`/${locale}/search`} className={buttonVariants({ variant: "outline", size: "sm" })}>
            Parcourir les annonces
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {favorites.map((f) => (
            <ListingCard
              key={f.id}
              listing={f.listing}
              locale={locale}
              dict={dict}
              defaultFavorited
            />
          ))}
        </div>
      )}
    </div>
  );
}
