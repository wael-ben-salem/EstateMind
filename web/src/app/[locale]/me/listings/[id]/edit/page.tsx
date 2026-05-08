import { notFound } from "next/navigation";
import { auth } from "@/lib/auth-helpers";
import { prisma } from "@/lib/prisma";
import { EditListingForm } from "@/components/listings/edit-listing-form";

export default async function EditListingPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  const numId = Number(id);
  if (!Number.isInteger(numId)) notFound();

  const session = await auth();
  const listing = await prisma.listing.findUnique({ where: { id: numId } });

  if (!listing || listing.ownerId !== Number(session!.user.id)) notFound();

  return <EditListingForm listing={listing} locale={locale} />;
}
