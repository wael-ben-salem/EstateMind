"use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2 } from "lucide-react";
import { useLang } from "@/contexts/lang";

export function SearchBar({ placeholder }: { placeholder?: string }) {
  const { t } = useLang();
  const [query, setQuery] = useState("");
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    startTransition(() => { router.push(`/search?q=${encodeURIComponent(query.trim())}`); });
  }

  return (
    <form onSubmit={submit}
          className="flex items-center w-full bg-white/95 backdrop-blur rounded-2xl
                     shadow-md overflow-hidden border border-navy/10">
      <Search size={16} className="ml-4 flex-shrink-0 text-navy/35" />
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder={placeholder ?? t.search.placeholder}
        className="flex-1 px-3 py-3 text-navy bg-transparent outline-none text-sm placeholder:text-navy/35"
      />
      <button type="submit" disabled={pending}
              className="m-1.5 px-4 py-2 bg-gold text-navy font-bold rounded-xl text-sm
                         hover:opacity-90 transition-opacity disabled:opacity-60 flex items-center gap-2 shrink-0">
        {pending ? <Loader2 size={14} className="animate-spin" /> : null}
        {t.hero.search}
      </button>
    </form>
  );
}
