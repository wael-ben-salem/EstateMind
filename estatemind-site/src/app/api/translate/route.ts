import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

export async function POST(req: NextRequest) {
  try {
    const { texts, target } = (await req.json()) as { texts: string[]; target: string };
    if (!texts?.length || !target) return NextResponse.json({ translations: texts });

    const translations = await Promise.all(
      texts.map(async (text) => {
        if (!text?.trim()) return text;
        const url =
          `https://translate.googleapis.com/translate_a/single` +
          `?client=gtx&sl=auto&tl=${encodeURIComponent(target)}&dt=t&q=${encodeURIComponent(text)}`;
        try {
          const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
          // Google response: [ [[translated, original, ...], ...], ... ]
          const data = (await res.json()) as unknown[][];
          const segments = (data[0] as unknown[][]).map((seg) => (seg as string[])[0] ?? "");
          return segments.join("") || text;
        } catch {
          return text;
        }
      })
    );

    return NextResponse.json({ translations });
  } catch {
    return NextResponse.json({ translations: [] });
  }
}
