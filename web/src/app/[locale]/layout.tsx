import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { notFound } from "next/navigation";
import "../globals.css";
import { getDict, isLocale, dirFor, LOCALES } from "@/i18n/dictionaries";
import { Header } from "@/components/site/header";
import { Footer } from "@/components/site/footer";
import { Toaster } from "@/components/ui/sonner";
import { LegalChatWidget } from "@/components/chat/legal-chat-widget";
import { SearchChatWidget } from "@/components/chat/search-chat-widget";
import { Providers } from "@/components/providers";

const geistSans = Geist({ variable: "--font-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Outliers", template: "%s · Outliers" },
  description: "L'immobilier tunisien, augmenté par l'IA",
};

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = await getDict(locale);

  return (
    <html
      lang={locale}
      dir={dirFor(locale)}
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Providers>
          <Header locale={locale} dict={dict} />
          <main className="flex-1">{children}</main>
          <Footer locale={locale} dict={dict} />
          <SearchChatWidget />
          <LegalChatWidget />
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
