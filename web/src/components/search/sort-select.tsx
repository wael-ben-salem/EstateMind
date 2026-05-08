"use client";

export function SortSelect({
  defaultValue,
  hidden,
  action,
}: {
  defaultValue: string;
  hidden: Record<string, string>;
  action: string;
}) {
  return (
    <form
      method="GET"
      action={action}
      className="flex items-center gap-2 text-sm text-muted-foreground"
    >
      {Object.entries(hidden).map(([k, v]) => (
        <input key={k} type="hidden" name={k} value={v} />
      ))}
      <label htmlFor="sort">Trier :</label>
      <select
        id="sort"
        name="sort"
        defaultValue={defaultValue}
        onChange={(e) => e.currentTarget.form?.submit()}
        className="rounded-lg border border-border bg-background px-2.5 py-1.5 text-sm hover:border-border/80 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors cursor-pointer"
      >
        <option value="newest">Nouveautés</option>
        <option value="price-asc">Prix croissant</option>
        <option value="price-desc">Prix décroissant</option>
      </select>
    </form>
  );
}
