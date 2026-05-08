import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { PostWizard } from "@/components/listings/post-wizard";

export default async function PostPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <PostWizard locale={locale} />;
}
