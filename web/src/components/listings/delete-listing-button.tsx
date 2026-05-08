"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Loader2 } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";

export function DeleteListingButton({ id }: { id: number }) {
  const router = useRouter();
  const [isPending, start] = useTransition();
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <div className="flex flex-col gap-1">
        <button
          type="button"
          disabled={isPending}
          onClick={() =>
            start(async () => {
              await fetch(`/api/listings/${id}`, { method: "DELETE" });
              router.refresh();
            })
          }
          className={`${buttonVariants({ variant: "destructive", size: "sm" })} text-xs`}
        >
          {isPending ? <Loader2 className="size-3 animate-spin" /> : "Confirmer"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className={`${buttonVariants({ variant: "ghost", size: "sm" })} text-xs`}
        >
          Annuler
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
      aria-label="Supprimer"
      title="Supprimer"
    >
      <Trash2 className="size-3.5 text-destructive" />
    </button>
  );
}
