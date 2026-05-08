import Link from "next/link";
import { Plus, ImageOff, Pencil } from "lucide-react";
import { auth } from "@/lib/auth-helpers";
import { prisma } from "@/lib/prisma";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { listingImages, formatPrice, listingTitle } from "@/lib/listing";
import type { Locale } from "@/i18n/dictionaries";
import { DeleteListingButton } from "@/components/listings/delete-listing-button";

export default async function MyListingsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const session = await auth();
  const userId = Number(session!.user.id);

  const items = await prisma.listing.findMany({
    where: { ownerId: userId },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Mes annonces</h1>
        <Link href={`/${locale}/me/post`} className={buttonVariants({ size: "sm" })}>
          <Plus className="size-4" />
          Nouvelle annonce
        </Link>
      </div>

      {items.length === 0 ? (
        <Card className="p-10 text-center text-sm text-muted-foreground">
          Vous n&apos;avez pas encore d&apos;annonce. Cliquez sur « Nouvelle annonce » pour commencer.
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((l) => {
            const img = listingImages(l)[0];
            const title = listingTitle(l);
            return (
              <Card key={l.id} className="flex gap-4 overflow-hidden p-3">
                <Link
                  href={`/${locale}/listings/${l.id}`}
                  className="relative block aspect-[4/3] w-32 shrink-0 overflow-hidden rounded-md bg-muted"
                >
                  {img ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={img} alt={title} className="h-full w-full object-cover" />
                  ) : (
                    <div className="grid h-full place-items-center text-muted-foreground">
                      <ImageOff className="size-5" />
                    </div>
                  )}
                </Link>
                <CardContent className="flex flex-1 flex-col justify-between p-0">
                  <div>
                    <Link href={`/${locale}/listings/${l.id}`} className="line-clamp-1 font-medium hover:underline">
                      {title}
                    </Link>
                    <p className="text-sm text-primary">
                      {formatPrice(l.prix, locale as Locale) ?? "Prix sur demande"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {[l.ville, l.gouvernerat].filter(Boolean).join(", ")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="secondary">
                      {l.contrat ?? "—"}
                    </Badge>
                    <span>· Créée le {l.createdAt.toLocaleDateString("fr-FR")}</span>
                  </div>
                </CardContent>
                <div className="flex flex-col gap-2">
                  <Link
                    href={`/${locale}/me/listings/${l.id}/edit`}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                    aria-label="Modifier"
                  >
                    <Pencil className="size-4" />
                  </Link>
                  <DeleteListingButton id={l.id} />
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
