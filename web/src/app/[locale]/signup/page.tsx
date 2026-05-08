import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { SignUpForm } from "@/components/auth/signup-form";

export default async function SignUpPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <SignUpForm locale={locale} />;
}
