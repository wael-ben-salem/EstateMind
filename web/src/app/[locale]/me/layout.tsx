import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { requireSession } from "@/lib/auth-helpers";

export default async function MeLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  await requireSession(`/${locale}/me`, locale);
  return <>{children}</>;
}
