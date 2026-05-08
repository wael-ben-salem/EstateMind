"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Heart, Loader2 } from "lucide-react";

export function FavoriteButton({
  listingId,
  defaultFavorited = false,
  locale = "fr",
}: {
  listingId: number;
  defaultFavorited?: boolean;
  locale?: string;
}) {
  const router = useRouter();
  const { data: session } = useSession();
  const [favorited, setFavorited] = useState(defaultFavorited);
  const [busy, setBusy] = useState(false);

  async function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!session?.user) {
      router.push(`/${locale}/signin?callbackUrl=${encodeURIComponent(location.pathname)}`);
      return;
    }
    if (busy) return;
    setBusy(true);
    // Optimistic update
    const prev = favorited;
    setFavorited(!prev);
    try {
      const r = await fetch(`/api/favorites/${listingId}`, { method: "POST" });
      if (!r.ok) throw new Error();
      const data = await r.json();
      setFavorited(Boolean(data.favorited));
    } catch {
      setFavorited(prev); // rollback
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={favorited ? "Retirer des favoris" : "Ajouter aux favoris"}
      className="absolute end-2 top-2 z-10 grid size-8 place-items-center rounded-full bg-background/90 backdrop-blur transition-all hover:scale-110 hover:bg-background"
    >
      {busy ? (
        <Loader2 className="size-4 animate-spin text-muted-foreground" />
      ) : (
        <Heart
          className={`size-4 transition-colors ${favorited ? "fill-destructive text-destructive" : "text-muted-foreground"}`}
        />
      )}
    </button>
  );
}
