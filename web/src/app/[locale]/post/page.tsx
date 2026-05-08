import { redirect } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { notFound } from "next/navigation";

export default async function PostPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  redirect(`/${locale}/me/post`);
}
