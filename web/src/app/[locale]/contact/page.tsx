import { isLocale } from "@/i18n/dictionaries";
import { notFound } from "next/navigation";
import { Mail } from "lucide-react";

export default async function ContactPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <div className="mb-8">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/6 px-4 py-1.5 text-xs font-medium text-primary">
          <Mail className="size-3" />
          Contact
        </div>
        <h1 className="text-4xl font-bold tracking-tight">Nous contacter</h1>
        <p className="mt-4 text-muted-foreground">
          Vous avez une question, un retour ou un bug à signaler ?
        </p>
      </div>

      <div className="rounded-2xl border border-border/60 bg-card p-8 text-sm text-muted-foreground">
        <p>
          Formulaire de contact à venir. Pour le moment, contactez l&apos;équipe via votre canal habituel.
        </p>
      </div>
    </div>
  );
}
