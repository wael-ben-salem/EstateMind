import Link from "next/link";
import { Construction } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function ComingSoon({
  title,
  phase,
  description,
  locale,
}: {
  title: string;
  phase: string;
  description?: string;
  locale: string;
}) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-20">
      <Card className="flex flex-col items-center gap-4 p-10 text-center">
        <div className="grid size-12 place-items-center rounded-full bg-secondary text-primary">
          <Construction className="size-6" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="text-sm uppercase tracking-wide text-muted-foreground">{phase}</p>
        {description && <p className="max-w-md text-balance text-muted-foreground">{description}</p>}
        <Link href={`/${locale}`} className={buttonVariants({ variant: "outline" })}>
          ← Retour à l&apos;accueil
        </Link>
      </Card>
    </div>
  );
}
