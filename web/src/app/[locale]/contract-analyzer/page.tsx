import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/dictionaries";
import { ContractAnalyzer } from "@/components/site/contract-analyzer";

export default async function ContractAnalyzerPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <ContractAnalyzer />;
}
