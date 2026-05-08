/**
 * Seed: stream `bigfinal_realestate_Cleaned.csv` (~1.96M rows) and random-sample
 * ~50k rows into the `Listing` table.
 *
 * Idempotent: wipes existing scrape-sourced listings first.
 * Run: `npm run db:seed`
 */
import { createReadStream } from "fs";
import { parse } from "csv-parse";
import { resolve } from "path";
import { PrismaClient } from "../src/generated/prisma";

const prisma = new PrismaClient();

const CSV_PATH = resolve(__dirname, "..", "..", "bigfinal_realestate_Cleaned.csv");
const TARGET = 50_000;
const TOTAL_HINT = 265_000;
const PROB = Math.min(1, TARGET / TOTAL_HINT);
const BATCH = 500;

function s(v: string | undefined): string | null {
  if (v === undefined) return null;
  const t = v.trim();
  if (t === "" || t === "nan" || t === "NaN") return null;
  return t;
}

function n(v: string | undefined): number | null {
  const t = s(v);
  if (t === null) return null;
  const x = parseFloat(t);
  return Number.isFinite(x) ? x : null;
}

function i(v: string | undefined): number | null {
  const x = n(v);
  return x === null ? null : Math.round(x);
}

function b(v: string | undefined): boolean | null {
  const t = s(v);
  if (t === null) return null;
  if (t === "true" || t === "True") return true;
  if (t === "false" || t === "False") return false;
  const x = parseFloat(t);
  if (!Number.isFinite(x)) return null;
  return x > 0;
}

async function main() {
  const t0 = Date.now();
  console.log(`Wiping existing listings...`);
  await prisma.listing.deleteMany({ where: { isUserCreated: false } });

  console.log(`Reading ${CSV_PATH}`);
  console.log(`Sampling p=${PROB.toFixed(4)} → ~${TARGET} rows`);

  const parser = createReadStream(CSV_PATH).pipe(
    parse({
      columns: true,
      skip_empty_lines: true,
      relax_quotes: true,
      relax_column_count: true,
      bom: true,
    })
  );

  let read = 0;
  let inserted = 0;
  let batch: any[] = [];

  const flush = async () => {
    if (!batch.length) return;
    const data = batch.splice(0);
    await prisma.listing.createMany({ data });
    inserted += data.length;
    if (inserted % 5000 < BATCH) {
      console.log(`  inserted ${inserted} (read ${read})`);
    }
  };

  for await (const row of parser as AsyncIterable<Record<string, string>>) {
    read++;
    if (Math.random() >= PROB) continue;

    batch.push({
      reference: s(row.reference),
      url: s(row.url),
      source: s(row.source),
      agence: s(row.agence),
      adresse: s(row.adresse),
      gouvernerat: s(row.gouvernerat),
      delegation: s(row.delegation),
      ville: s(row.ville),
      localite: s(row.localite),
      codep: s(row.codep),
      latitude: n(row.latitude),
      longitude: n(row.longitude),
      geoPrecision: s(row.geo_precision),
      type: s(row.type),
      contrat: s(row.contrat),
      prix: n(row.prix),
      prixOriginal: n(row.prix_original),
      prixM2: n(row.prix_m2),
      prixQ75Contrat: n(row.prix_q75_contrat),
      surface: n(row.surface),
      surfaceOriginal: n(row.surface_original),
      superficieTerrain: n(row.superficie_terrain),
      pieces: i(row.pieces),
      piecesOriginal: i(row.pieces_original),
      etage: i(row.etage),
      etageOriginal: i(row.etage_original),
      anneeConstr: i(row.annee_constr),
      hasAscenseur: b(row.has_ascenseur),
      hasBalcon: b(row.has_balcon),
      hasChaffage: b(row.has_chaffage),
      hasClimatisation: b(row.has_climatisation),
      hasGarage: b(row.has_garage),
      hasGardien: b(row.has_gardien),
      hasJardin: b(row.has_jardin),
      hasParking: b(row.has_parking),
      hasPiscine: b(row.has_piscine),
      hasTerrasse: b(row.has_terrasse),
      cuisine: s(row.cuisine),
      salleDeBain: s(row.salle_de_bain),
      chauffage: s(row.chauffage),
      climatisation: s(row.climatisation),
      installationsSportives: s(row.installations_sportives),
      bus: i(row.bus),
      railway: i(row.railway),
      ecole: i(row.ecole),
      hopital: i(row.hopital),
      pharmacie: i(row.pharmacie),
      magasin: i(row.magasin),
      marche: i(row.marche),
      restaurant: i(row.restaurant),
      standing: s(row.standing),
      hautStanding: b(row.haut_standing),
      bonEntourage: b(row.bon_entourage),
      bonEntourageLlm: s(row.bon_entourage_llm),
      tel: s(row.tel),
      titre: s(row.titre),
      description: s(row.description),
      descClean: s(row.desc_clean),
      caracBlock: s(row.carac_block),
      caracteristiques: s(row.caracteristiques),
      contratCarac: s(row.contrat_carac),
      surfaceCarac: s(row.surface_carac),
      codePostalCarac: s(row.code_postal_carac),
      fonds: s(row.fonds),
      constructible: s(row.constructible),
      pleinAir: s(row.plein_air),
      service: s(row.service),
      images: s(row.images),
      otherData: s(row.other_data),
      datePublication: s(row.date_publication),
      pubYear: i(row.pub_year),
      pubMonth: i(row.pub_month),
      isUserCreated: false,
    });

    if (batch.length >= BATCH) await flush();
  }
  await flush();

  const dt = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nDone. Read ${read} rows, inserted ${inserted} in ${dt}s.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
