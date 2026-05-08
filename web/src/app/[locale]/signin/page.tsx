import { Suspense } from "react";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { SignInForm } from "@/components/auth/signin-form";

export default async function SignInPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <Suspense>
      <SignInForm locale={locale} />
    </Suspense>
  );
}
