import { NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { auth } from "../../services/api";
import { useLang } from "../../contexts/LangContext";

const NAV_KEYS = [
  { to: "/",          icon: "⬛", key: "overview" },
  { to: "/map",       icon: "🗺️",  key: "map" },
  { to: "/analytics", icon: "📊", key: "analytics" },
  { to: "/scrapers",  icon: "🤖", key: "scrapers" },
  { to: "/pipeline",  icon: "⚙️",  key: "pipeline" },
  { to: "/listings",  icon: "🏠", key: "listings" },
  { to: "/powerbi",   icon: "📈", key: "powerbi" },
];

const GOLD   = "oklch(0.77 0.18 68)";
const NAVY   = "oklch(0.18 0.065 260)";
const MUTED  = "oklch(0.65 0.02 260)";
const ACTIVE_BG = "oklch(0.77 0.18 68 / 0.12)";

export default function Sidebar({ collapsed, onToggle }) {
  const { t } = useLang();

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 220 }}
      transition={{ duration: 0.25 }}
      style={{
        background: NAVY,
        height: "100vh",
        position: "fixed",
        left: 0, top: 0,
        display: "flex",
        flexDirection: "column",
        zIndex: 100,
        overflow: "hidden",
        boxShadow: "2px 0 12px oklch(0.18 0.065 260 / 0.3)",
        borderRight: `3px solid ${GOLD}`,
      }}
    >
      {/* Gold top accent */}
      <div style={{ height: 3, background: GOLD, flexShrink: 0 }} />

      {/* Logo */}
      <div style={{ padding: "18px 16px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <AnimatePresence>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div style={{ fontFamily: "Playfair Display, Georgia, serif", fontWeight: 800, fontSize: 18, color: GOLD, letterSpacing: "-0.5px" }}>
                Estate<span style={{ color: "#fff" }}>Mind</span>
              </div>
              <div style={{ fontSize: 10, color: MUTED, marginTop: 2, fontFamily: "Inter, sans-serif" }}>{t.nav.admin_dashboard}</div>
            </motion.div>
          )}
        </AnimatePresence>
        {collapsed && (
          <div style={{ color: GOLD, fontWeight: 800, fontSize: 16, textAlign: "center", fontFamily: "Playfair Display, serif" }}>E</div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 0", overflowY: "auto" }}>
        {NAV_KEYS.map(({ to, icon, key }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "11px 16px",
              margin: "2px 8px",
              borderRadius: 8,
              color: isActive ? GOLD : MUTED,
              background: isActive ? ACTIVE_BG : "transparent",
              borderLeft: isActive ? `3px solid ${GOLD}` : "3px solid transparent",
              transition: "all 0.18s",
              textDecoration: "none",
              fontSize: 13,
              fontWeight: 500,
              fontFamily: "Inter, sans-serif",
              whiteSpace: "nowrap",
              overflow: "hidden",
            })}
          >
            <span style={{ fontSize: 16, flexShrink: 0 }}>{icon}</span>
            <AnimatePresence>
              {!collapsed && (
                <motion.span initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: "auto" }} exit={{ opacity: 0, width: 0 }}>
                  {t.nav[key]}
                </motion.span>
              )}
            </AnimatePresence>
          </NavLink>
        ))}
      </nav>

      {/* Footer links */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", padding: "8px 0" }}>
        <AnimatePresence>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <a
                href="http://localhost:3001"
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 16px", margin: "2px 8px", borderRadius: 8,
                  color: MUTED, fontSize: 12, fontFamily: "Inter, sans-serif",
                  textDecoration: "none", transition: "color 0.18s",
                }}
                onMouseEnter={e => e.currentTarget.style.color = "#fff"}
                onMouseLeave={e => e.currentTarget.style.color = MUTED}
              >
                {t.nav.back_to_site}
              </a>
              <button
                onClick={() => auth.logout()}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 16px", margin: "2px 8px", borderRadius: 8,
                  background: "transparent", border: "none",
                  color: MUTED, fontSize: 12, fontFamily: "Inter, sans-serif",
                  cursor: "pointer", width: "calc(100% - 16px)", textAlign: "left",
                  transition: "color 0.18s",
                }}
                onMouseEnter={e => e.currentTarget.style.color = "#ff6b6b"}
                onMouseLeave={e => e.currentTarget.style.color = MUTED}
              >
                ⏻ {t.nav.logout}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        style={{
          background: "rgba(255,255,255,0.05)",
          border: "none",
          color: MUTED,
          padding: "14px",
          cursor: "pointer",
          fontSize: 14,
          transition: "background 0.2s",
          flexShrink: 0,
        }}
        onMouseEnter={e => e.target.style.background = "rgba(255,255,255,0.1)"}
        onMouseLeave={e => e.target.style.background = "rgba(255,255,255,0.05)"}
      >
        {collapsed ? "▶" : "◀"}
      </button>
    </motion.aside>
  );
}
