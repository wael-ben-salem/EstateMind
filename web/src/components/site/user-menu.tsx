"use client";

import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { User, LogOut, Plus, Heart, LayoutDashboard, FileSearch } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { buttonVariants } from "@/components/ui/button";

export function UserMenu({ locale }: { locale: string }) {
  const { data: session, status } = useSession();
  const link = (p: string) => `/${locale}${p}`;

  if (status === "loading") {
    return <div className="size-8 animate-pulse rounded-full bg-secondary" />;
  }

  if (!session?.user) {
    return (
      <Link href={link("/signin")} className={buttonVariants({ size: "sm" })}>
        Se connecter
      </Link>
    );
  }

  const initial = (session.user.name?.[0] ?? session.user.email?.[0] ?? "?").toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <Avatar className="size-8">
          <AvatarFallback className="bg-primary/10 text-primary">{initial}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium text-foreground">{session.user.name ?? "Utilisateur"}</span>
              <span className="text-xs font-normal text-muted-foreground">{session.user.email}</span>
            </div>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href={link("/me")} />}>
          <LayoutDashboard className="size-4" />
          Tableau de bord
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href={link("/me/post")} />}>
          <Plus className="size-4" />
          Publier une annonce
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href={link("/favorites")} />}>
          <Heart className="size-4" />
          Mes favoris
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href={link("/me/listings")} />}>
          <User className="size-4" />
          Mes annonces
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href={link("/contract-analyzer")} />}>
          <FileSearch className="size-4" />
          Analyser un contrat
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => signOut({ callbackUrl: link("/") })}>
          <LogOut className="size-4" />
          Déconnexion
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
