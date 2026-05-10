import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { LegalChat } from "@/components/legal-chat";
import { RecommendWidget } from "@/components/recommend-widget";
import { LangProvider } from "@/contexts/lang";
import "./globals.css";

const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair", display: "swap" });
const inter    = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "EstateMind — Immobilier Tunisien par IA",
  description: "Trouvez votre bien idéal en Tunisie grâce à l'intelligence artificielle.",
  icons: { icon: "/logo.png", apple: "/logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" data-scroll-behavior="smooth" suppressHydrationWarning className={`${playfair.variable} ${inter.variable}`}>
      <body>
        <Providers>
          <LangProvider>
            {children}
            <RecommendWidget />
            <LegalChat />
          </LangProvider>
        </Providers>
      </body>
    </html>
  );
}
