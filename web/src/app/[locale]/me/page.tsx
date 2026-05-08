import Link from "next/link";
import { Plus, List, Heart, LogOut } from "lucide-react";
import { auth } from "@/lib/auth-helpers";
import { prisma } from "@/lib/prisma";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { SignOutButton } from "@/components/auth/signout-button";

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const session = await auth();
  const userId = Number(session!.user.id);

  const [listingCount, favoriteCount] = await Promise.all([
    prisma.listing.count({ where: { ownerId: userId } }),
    prisma.favorite.count({ where: { userId } }),
  ]);

  const link = (p: string) => `/${locale}${p}`;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Bonjour</p>
          <h1 className="text-2xl font-semibold">{session!.user.name ?? session!.user.email}</h1>
          <Badge variant="secondary" className="mt-2 capitalize">
            {session!.user.role ?? "buyer"}
          </Badge>
        </div>
        <SignOutButton locale={locale} />
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Plus className="size-4 text-primary" />
              Publier une annonce
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-sm text-muted-foreground">
              Téléchargez vos photos, l&apos;IA pré-remplit la description et les caractéristiques.
            </p>
            <Link href={link("/me/post")} className={buttonVariants({ size: "sm" })}>
              Commencer
            </Link>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <List className="size-4 text-primary" />
              Mes annonces
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-3xl font-semibold text-foreground">{listingCount}</p>
            <Link href={link("/me/listings")} className={buttonVariants({ variant: "outline", size: "sm" })}>
              Gérer
            </Link>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Heart className="size-4 text-primary" />
              Mes favoris
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-3xl font-semibold text-foreground">{favoriteCount}</p>
            <Link href={link("/favorites")} className={buttonVariants({ variant: "outline", size: "sm" })}>
              Voir
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
