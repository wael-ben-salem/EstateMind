import { useLang } from "../contexts/LangContext";

const FLAGS = { fr: "🇫🇷", ar: "🇹🇳", en: "🇬🇧" };
const LABELS = { fr: "FR", ar: "AR", en: "EN" };

export default function LangSwitcher() {
  const { locale, setLocale } = useLang();

  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
      {["fr", "ar", "en"].map((l) => (
        <button
          key={l}
          onClick={() => setLocale(l)}
          title={l.toUpperCase()}
          style={{
            padding: "4px 8px",
            borderRadius: 6,
            border: locale === l
              ? "1.5px solid oklch(0.77 0.18 68)"
              : "1.5px solid oklch(0.18 0.065 260 / 0.12)",
            background: locale === l ? "oklch(0.77 0.18 68 / 0.1)" : "transparent",
            color: locale === l ? "oklch(0.18 0.065 260)" : "oklch(0.55 0.03 260)",
            fontFamily: "Inter, sans-serif",
            fontSize: 11,
            fontWeight: locale === l ? 700 : 500,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 3,
            transition: "all 0.15s",
          }}
        >
          <span>{FLAGS[l]}</span>
          <span>{LABELS[l]}</span>
        </button>
      ))}
    </div>
  );
}
