import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";

export function Pagination({
  basePath,
  searchParams,
  currentPage,
  totalPages,
}: {
  basePath: string;
  searchParams: Record<string, string | undefined>;
  currentPage: number;
  totalPages: number;
}) {
  if (totalPages <= 1) return null;

  const buildHref = (page: number) => {
    const params = new URLSearchParams();
    Object.entries(searchParams).forEach(([k, v]) => {
      if (v && k !== "page") params.set(k, v);
    });
    if (page > 1) params.set("page", String(page));
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  // Build a compact page list: 1, ..., n-1, n, n+1, ..., last
  const pages: (number | "…")[] = [];
  const push = (p: number | "…") => {
    if (pages[pages.length - 1] !== p) pages.push(p);
  };
  push(1);
  if (currentPage - 2 > 2) push("…");
  for (let p = Math.max(2, currentPage - 1); p <= Math.min(totalPages - 1, currentPage + 1); p++) {
    push(p);
  }
  if (currentPage + 2 < totalPages - 1) push("…");
  if (totalPages > 1) push(totalPages);

  return (
    <nav className="mt-8 flex items-center justify-center gap-1">
      {currentPage > 1 && (
        <Link
          href={buildHref(currentPage - 1)}
          className={buttonVariants({ variant: "outline", size: "sm" })}
          aria-label="Page précédente"
        >
          <ChevronLeft className="size-3.5" />
        </Link>
      )}
      {pages.map((p, i) =>
        p === "…" ? (
          <span key={`e${i}`} className="px-2 text-sm text-muted-foreground">…</span>
        ) : (
          <Link
            key={p}
            href={buildHref(p)}
            className={buttonVariants({
              variant: p === currentPage ? "secondary" : "ghost",
              size: "sm",
            })}
          >
            {p}
          </Link>
        )
      )}
      {currentPage < totalPages && (
        <Link
          href={buildHref(currentPage + 1)}
          className={buttonVariants({ variant: "outline", size: "sm" })}
          aria-label="Page suivante"
        >
          <ChevronRight className="size-3.5" />
        </Link>
      )}
    </nav>
  );
}
