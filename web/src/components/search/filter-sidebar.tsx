import { buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";

export type SearchFilters = {
  q?: string;
  gouvernerat?: string;
  type?: string;
  contrat?: string;
  pieces?: string;
  priceMin?: string;
  priceMax?: string;
  sort?: string;
  photos?: string;
};

const selectCls =
  "mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground appearance-none cursor-pointer hover:border-border/80 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors";

const labelCls = "block text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60";

export function FilterSidebar({
  locale,
  filters,
  gouvernerats,
  types,
}: {
  locale: string;
  filters: SearchFilters;
  gouvernerats: string[];
  types: string[];
}) {
  return (
    <div className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur-sm">
      <p className="mb-4 text-sm font-semibold">Filtres</p>
      <form method="GET" action={`/${locale}/search`} className="space-y-4">
        {filters.q && <input type="hidden" name="q" value={filters.q} />}
        {filters.sort && <input type="hidden" name="sort" value={filters.sort} />}

        <div>
          <label className={labelCls}>Contrat</label>
          <select name="contrat" defaultValue={filters.contrat ?? ""} className={selectCls}>
            <option value="">Tous</option>
            <option value="vente">Vente</option>
            <option value="location">Location</option>
          </select>
        </div>

        <div>
          <label className={labelCls}>Type</label>
          <select name="type" defaultValue={filters.type ?? ""} className={selectCls}>
            <option value="">Tous</option>
            {types.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelCls}>Gouvernorat</label>
          <select name="gouvernerat" defaultValue={filters.gouvernerat ?? ""} className={selectCls}>
            <option value="">Tous</option>
            {gouvernerats.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelCls}>Pièces minimum</label>
          <select name="pieces" defaultValue={filters.pieces ?? ""} className={selectCls}>
            <option value="">Indifférent</option>
            {["1","2","3","4","5"].map((n) => (
              <option key={n} value={n}>{n}+</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className={labelCls}>Prix min</label>
            <Input
              type="number"
              name="priceMin"
              defaultValue={filters.priceMin}
              placeholder="0"
              className="mt-1 rounded-lg"
            />
          </div>
          <div>
            <label className={labelCls}>Prix max</label>
            <Input
              type="number"
              name="priceMax"
              defaultValue={filters.priceMax}
              placeholder="∞"
              className="mt-1 rounded-lg"
            />
          </div>
        </div>

        <div>
          <label className={labelCls}>Photos</label>
          <select name="photos" defaultValue={filters.photos ?? "0"} className={selectCls}>
            <option value="1">Avec photos uniquement</option>
            <option value="0">Tous les biens</option>
          </select>
        </div>

        <div className="flex flex-col gap-2 pt-1">
          <button
            type="submit"
            className={`${buttonVariants({ size: "sm" })} w-full bg-gradient-to-r from-blue-500 to-violet-600 text-white border-0 hover:from-blue-400 hover:to-violet-500`}
          >
            Appliquer
          </button>
          <Link
            href={`/${locale}/search`}
            className={`${buttonVariants({ variant: "ghost", size: "sm" })} w-full text-muted-foreground`}
          >
            Réinitialiser
          </Link>
        </div>
      </form>
    </div>
  );
}
