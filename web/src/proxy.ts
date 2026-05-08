import { NextResponse, type NextRequest } from "next/server";

const LOCALES = ["fr", "ar", "en"] as const;
const DEFAULT_LOCALE = "fr";

/**
 * Next.js 16 renamed `middleware.ts` → `proxy.ts`.
 * This redirects any unprefixed path (e.g. `/`, `/search`) to the default locale.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasLocale = LOCALES.some(
    (l) => pathname === `/${l}` || pathname.startsWith(`/${l}/`)
  );
  if (hasLocale) return;

  const url = request.nextUrl.clone();
  url.pathname = `/${DEFAULT_LOCALE}${pathname === "/" ? "" : pathname}`;
  return NextResponse.redirect(url);
}

export const config = {
  // Skip Next internals, API routes, and any path with a file extension (favicon, png, etc.).
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
