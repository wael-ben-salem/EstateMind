import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth-helpers";

/** POST toggles the favorite state for the current user + given listing. */
export async function POST(
  _req: Request,
  ctx: { params: Promise<{ listingId: string }> }
) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const userId = Number(session.user.id);
  const listingId = Number((await ctx.params).listingId);
  if (!Number.isInteger(listingId)) {
    return NextResponse.json({ error: "invalid id" }, { status: 400 });
  }

  const existing = await prisma.favorite.findUnique({
    where: { userId_listingId: { userId, listingId } },
  });

  if (existing) {
    await prisma.favorite.delete({ where: { id: existing.id } });
    return NextResponse.json({ favorited: false });
  } else {
    // Make sure the listing exists before favoriting
    const listing = await prisma.listing.findUnique({ where: { id: listingId } });
    if (!listing) {
      return NextResponse.json({ error: "listing not found" }, { status: 404 });
    }
    await prisma.favorite.create({ data: { userId, listingId } });
    return NextResponse.json({ favorited: true });
  }
}
