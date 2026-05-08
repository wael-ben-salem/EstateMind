"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { signIn } from "next-auth/react";
import { Loader2, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buttonVariants } from "@/components/ui/button";

const DEMO_EMAIL = "demo@outliers.local";
const DEMO_PASSWORD = "demo-pass";

export function SignInForm({ locale }: { locale: string }) {
  const router = useRouter();
  const search = useSearchParams();
  const callbackUrl = search.get("callbackUrl") ?? `/${locale}/me`;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handle(e: React.FormEvent, creds: { email: string; password: string }) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const r = await signIn("credentials", { ...creds, redirect: false });
    setLoading(false);
    if (r?.ok) {
      router.push(callbackUrl);
      router.refresh();
    } else {
      setError("Identifiants invalides.");
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <Card>
        <CardHeader>
          <CardTitle>Connexion</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <button
            type="button"
            disabled={loading}
            onClick={(e) => handle(e, { email: DEMO_EMAIL, password: DEMO_PASSWORD })}
            className={`${buttonVariants({ variant: "outline" })} w-full`}
          >
            <Sparkles className="size-4 text-primary" />
            Connexion démo (vendeur)
          </button>

          <div className="relative my-2 text-center text-xs text-muted-foreground">
            <span className="bg-card px-2">ou avec votre email</span>
            <hr className="absolute inset-x-0 top-1/2 -z-10 border-border" />
          </div>

          <form onSubmit={(e) => handle(e, { email, password })} className="space-y-3">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@exemple.tn"
              />
            </div>
            <div>
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <button type="submit" disabled={loading} className={`${buttonVariants()} w-full`}>
              {loading && <Loader2 className="size-4 animate-spin" />}
              Se connecter
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Pas de compte ?{" "}
            <Link href={`/${locale}/signup`} className="text-primary hover:underline">
              Créer un compte
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
