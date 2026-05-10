import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../../contexts/LangContext";
import LangSwitcher from "../LangSwitcher";

export default function TopBar({ title, subtitle }) {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const { t } = useLang();

  function onSearch(e) {
    e.preventDefault();
    if (search.trim()) navigate(`/listings?search=${encodeURIComponent(search.trim())}`);
  }

  return (
    <header style={{
      height: 64,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 28px",
      background: "#fff",
      borderBottom: "1px solid oklch(0.18 0.065 260 / 0.08)",
      borderTop: "3px solid oklch(0.77 0.18 68)",
      position: "sticky",
      top: 0,
      zIndex: 50,
    }}>
      <div>
        <div style={{ fontFamily: "Playfair Display, Georgia, serif", fontWeight: 700, fontSize: 17, color: "oklch(0.18 0.065 260)" }}>{title}</div>
        {subtitle && <div style={{ fontSize: 12, color: "oklch(0.55 0.03 260)", marginTop: 1, fontFamily: "Inter, sans-serif" }}>{subtitle}</div>}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <LangSwitcher />
        <form onSubmit={onSearch} style={{ display: "flex", gap: 8 }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t.topbar.search_placeholder}
            style={{
              padding: "7px 14px",
              border: "1.5px solid oklch(0.18 0.065 260 / 0.12)",
              borderRadius: 8,
              fontFamily: "Inter, sans-serif",
              fontSize: 13,
              width: 220,
              background: "oklch(0.97 0.008 85)",
              outline: "none",
              color: "oklch(0.18 0.065 260)",
            }}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: "7px 16px", fontSize: 13 }}>🔍</button>
        </form>
      </div>
    </header>
  );
}
