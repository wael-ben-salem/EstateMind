import { prisma } from "@/lib/prisma";
import { SearchContent } from "./search-content";

const PAGE_SIZE = 12;
const TYPES    = ["Appartement","Villa","Maison","Terrain","Bureau","Local commercial","Studio","Ferme"];
const CONTRATS = ["Vente","Location","Location saisonnière"];
const GOVS     = ["Tunis","Ariana","Ben Arous","Manouba","Nabeul","Sousse","Sfax","Monastir","Mahdia","Bizerte","Béja","Jendouba","Siliana","Kef","Kairouan","Kasserine","Sidi Bouzid","Gafsa","Tozeur","Kébili","Gabès","Médenine","Tataouine","Zaghouan"];

// Extended city/area list for NLP parsing
const ALL_LOCATIONS = [
  ...GOVS,
  "Hammamet","Djerba","Carthage","La Marsa","Sidi Bou Saïd","Marsa","Menzah",
  "El Menzah","Ennasr","Lac","Berges du Lac","Mégrine","Radès","La Soukra",
  "Manar","Cité El Khadra","Bardo","Médina","Lafayette","Montplaisir",
  "Les Jardins de Carthage","Les Berges du Lac","Ain Zaghouan",
];

interface NLPResult {
  types: string[];
  contrat: string;
  gouvernerat: string;
  pieces: number | undefined;
  minPrix: number | undefined;
  maxPrix: number | undefined;
  keywords: string;
}

function parseNaturalQuery(q: string): NLPResult {
  const result: NLPResult = {
    types: [], contrat: "", gouvernerat: "",
    pieces: undefined, minPrix: undefined, maxPrix: undefined,
    keywords: q,
  };

  // --- Property type ---
  const typePatterns: [RegExp, string][] = [
    [/\bappart(?:ement)?\b/i,      "Appartement"],
    [/\bvilla\b/i,                  "Villa"],
    [/\bmaison\b/i,                 "Maison"],
    [/\bterrain\b/i,                "Terrain"],
    [/\bstudio\b/i,                 "Studio"],
    [/\bbureau\b/i,                 "Bureau"],
    [/\blocal\s+commercial\b/i,     "Local commercial"],
    [/\bferme\b/i,                  "Ferme"],
    // Arabic
    [/\bشقة\b/,                     "Appartement"],
    [/\bفيلا\b/,                    "Villa"],
    [/\bمنزل\b/,                    "Maison"],
    [/\bأرض\b/,                     "Terrain"],
    [/\bستوديو\b/,                  "Studio"],
    [/\bمكتب\b/,                    "Bureau"],
  ];
  for (const [re, type] of typePatterns) {
    if (re.test(q)) result.types.push(type);
  }

  // --- Contract ---
  if (/\b(à louer|louer|en location|location|rent|rental|للإيجار)\b/i.test(q)) result.contrat = "Location";
  else if (/\b(à vendre|vente|acheter|buy|purchase|للبيع|شراء)\b/i.test(q)) result.contrat = "Vente";
  if (/\bsaisonn/i.test(q)) result.contrat = "Location saisonnière";

  // --- Rooms/pieces ---
  const piecesMatch =
    q.match(/(\d+)\s*(?:pièces?|pieces?|chambres?|rooms?)\b/i) ||
    q.match(/\bS\+(\d+)\b/i) ||
    q.match(/\bF(\d)\b/i);
  if (piecesMatch) result.pieces = parseInt(piecesMatch[1] ?? piecesMatch[2] ?? "0");

  // --- Price ---
  const priceNum = (s: string) => {
    const cleaned = s.replace(/[\s, ]/g, "").replace(/\.(?=\d{3})/g, "");
    const n = parseFloat(cleaned.replace(/k$/i, "")) * (/k$/i.test(cleaned) ? 1000 : 1);
    return isNaN(n) ? undefined : n;
  };
  const maxMatch = q.match(/(?:moins(?:\s+de)?|max(?:imum)?|budget|jusqu[''']?à?|up\s+to|≤)\s*([\d\s.,kK]+)\s*(?:TND|DT|dinar)?/i);
  if (maxMatch) result.maxPrix = priceNum(maxMatch[1]);
  const minMatch = q.match(/(?:à partir\s+de|min(?:imum)?|au moins|from|≥)\s*([\d\s.,kK]+)\s*(?:TND|DT|dinar)?/i);
  if (minMatch) result.minPrix = priceNum(minMatch[1]);

  // --- Location ---
  for (const loc of ALL_LOCATIONS) {
    if (new RegExp(`\\b${loc.replace(/['']/g, "[''']?")}\\b`, "i").test(q)) {
      result.gouvernerat = loc;
      break;
    }
  }

  // --- Remaining keywords (strip extracted tokens) ---
  let kw = q;
  if (result.types.length)
    kw = kw.replace(/\b(appart(?:ement)?|villa|maison|terrain|studio|bureau|local\s+commercial|ferme)\b/gi, "");
  if (result.contrat)
    kw = kw.replace(/\b(à louer|louer|en location|location|rent|rental|à vendre|vente|acheter|buy|purchase|saisonn\w*)\b/gi, "");
  kw = kw.replace(/\d+\s*(?:pièces?|pieces?|chambres?|rooms?)\b/gi, "");
  kw = kw.replace(/\bS\+\d+\b/gi, "").replace(/\bF\d\b/gi, "");
  if (result.gouvernerat)
    kw = kw.replace(new RegExp(`\\b${result.gouvernerat}\\b`, "i"), "");
  // Strip stop words and cleanup
  kw = kw.replace(/\b(à|de|avec|et|en|le|la|les|au|aux|un|une|des|du|sur|par|pour|dans|près)\b/gi, "");
  result.keywords = kw.replace(/\s{2,}/g, " ").trim();

  return result;
}

interface SearchParams {
  q?: string; type?: string | string[]; contrat?: string; gouvernerat?: string;
  min_prix?: string; max_prix?: string; pieces?: string; page?: string;
}

export default async function SearchPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const sp      = await searchParams;
  const page    = Math.max(1, parseInt(sp.page ?? "1", 10));
  const q       = sp.q?.trim() ?? "";
  const types   = Array.isArray(sp.type) ? sp.type : sp.type ? [sp.type] : [];
  const contrat = sp.contrat?.trim() ?? "";
  const gov     = sp.gouvernerat?.trim() ?? "";
  const minP    = sp.min_prix ? parseFloat(sp.min_prix) : undefined;
  const maxP    = sp.max_prix ? parseFloat(sp.max_prix) : undefined;
  const pieces  = sp.pieces ? parseInt(sp.pieces, 10) : undefined;

  // Parse natural language from q, then merge with explicit filters (explicit wins)
  const nlp = q ? parseNaturalQuery(q) : null;

  const effectiveTypes   = types.length   > 0       ? types   : (nlp?.types   ?? []);
  const effectiveContrat = contrat                   ? contrat : (nlp?.contrat ?? "");
  const effectiveGov     = gov                       ? gov     : (nlp?.gouvernerat ?? "");
  const effectivePieces  = pieces !== undefined      ? pieces  : nlp?.pieces;
  const effectiveMinP    = minP   !== undefined      ? minP    : nlp?.minPrix;
  const effectiveMaxP    = maxP   !== undefined      ? maxP    : nlp?.maxPrix;
  const kw               = nlp?.keywords ?? q; // residual keywords after NLP extraction

  const where: Record<string, unknown> = {};
  if (kw) where.OR = [
    { titre:       { contains: kw } },
    { description: { contains: kw } },
    { ville:       { contains: kw } },
    { gouvernerat: { contains: kw } },
    { adresse:     { contains: kw } },
  ];
  if (effectiveTypes.length)  where.type       = { in: effectiveTypes };
  if (effectiveContrat)       where.contrat    = effectiveContrat;
  if (effectiveGov)           where.gouvernerat = effectiveGov;
  if (effectiveMinP !== undefined || effectiveMaxP !== undefined)
    where.prix = { ...(effectiveMinP ? { gte: effectiveMinP } : {}), ...(effectiveMaxP ? { lte: effectiveMaxP } : {}) };
  if (effectivePieces)        where.pieces     = { gte: effectivePieces };

  const [listings, total] = await Promise.all([
    prisma.listing.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip:    (page - 1) * PAGE_SIZE,
      take:    PAGE_SIZE,
      select:  { id: true, titre: true, prix: true, gouvernerat: true, ville: true, type: true, contrat: true, surface: true, pieces: true, images: true },
    }),
    prisma.listing.count({ where }),
  ]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <SearchContent
      listings={listings} total={total} page={page} totalPages={totalPages}
      q={q} types={types} contrat={contrat} gov={gov}
      minP={minP?.toString() ?? ""} maxP={maxP?.toString() ?? ""}
      pieces={pieces?.toString() ?? ""}
      TYPES={TYPES} CONTRATS={CONTRATS} GOVS={GOVS}
    />
  );
}
