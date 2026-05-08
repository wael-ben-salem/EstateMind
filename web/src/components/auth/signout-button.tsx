"use client";

import { signOut } from "next-auth/react";
import { LogOut } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";

export function SignOutButton({ locale }: { locale: string }) {
  return (
    <button
      type="button"
      onClick={() => signOut({ callbackUrl: `/${locale}` })}
      className={buttonVariants({ variant: "ghost", size: "sm" })}
    >
      <LogOut className="size-4" />
      Déconnexion
    </button>
  );
}
