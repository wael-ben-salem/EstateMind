import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";

export async function auth() {
  return getServerSession(authOptions);
}

/** Redirects to /signin?callbackUrl=... if not signed in. Returns the session otherwise. */
export async function requireSession(callbackUrl: string, locale = "fr") {
  const session = await auth();
  if (!session?.user) {
    redirect(`/${locale}/signin?callbackUrl=${encodeURIComponent(callbackUrl)}`);
  }
  return session;
}
