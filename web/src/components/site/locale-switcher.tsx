"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "@/components/ui/button";

const LOCALES = ["fr", "ar", "en"] as const;
type Locale = (typeof LOCALES)[number];

export function LocaleSwitcher({ current }: { current: Locale }) {
  const pathname = usePathname();
  const stripped = pathname.replace(/^\/(fr|ar|en)(?=\/|$)/, "") || "/";

  return (
    <div className="flex items-center gap-1 text-xs">
      {LOCALES.map((loc) => (
        <Link
          key={loc}
          href={`/${loc}${stripped === "/" ? "" : stripped}`}
          className={`${buttonVariants({ size: "xs", variant: loc === current ? "secondary" : "ghost" })} uppercase`}
        >
          {loc}
        </Link>
      ))}
    </div>
  );
}
