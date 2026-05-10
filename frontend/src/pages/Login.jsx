import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../contexts/LangContext";
import LangSwitcher from "../components/LangSwitcher";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();
  const { t } = useLang();
  const L = t.login;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Identifiants incorrects"); return; }
      localStorage.setItem("em_token", data.token);
      navigate("/", { replace: true });
    } catch {
      setError(L.error_server);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "Inter, sans-serif" }}>

      {/* Left panel — navy */}
      <div style={{
        flex: "0 0 42%",
        background: "oklch(0.18 0.065 260)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 48px",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: "oklch(0.77 0.18 68)" }} />
        <div style={{
          position: "absolute", bottom: -80, right: -80,
          width: 300, height: 300, borderRadius: "50%",
          background: "oklch(0.26 0.065 260 / 0.4)",
        }} />

        <div style={{ position: "relative", textAlign: "center", maxWidth: 320 }}>
          <div style={{
            fontFamily: "Playfair Display, Georgia, serif", fontWeight: 800,
            fontSize: 32, color: "oklch(0.77 0.18 68)", letterSpacing: "-0.5px", marginBottom: 8,
          }}>
            Estate<span style={{ color: "#fff" }}>Mind</span>
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 48 }}>
            {L.brand_sub}
          </div>

          <div style={{
            fontFamily: "Playfair Display, Georgia, serif", fontWeight: 700,
            fontSize: 22, color: "#fff", lineHeight: 1.4, marginBottom: 16,
            whiteSpace: "pre-line",
          }}>
            {L.panel_title}
          </div>
          <p style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", lineHeight: 1.7 }}>
            {L.panel_sub}
          </p>

          <div style={{ marginTop: 48, padding: "16px 24px", background: "oklch(0.26 0.065 260 / 0.6)", borderRadius: 12, textAlign: "left" }}>
            <div style={{ fontSize: 10, color: "oklch(0.77 0.18 68)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
              Données en temps réel
            </div>
            <div style={{ fontSize: 28, fontFamily: "Playfair Display, serif", fontWeight: 700, color: "#fff" }}>264 847</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>{L.stats_label}</div>
          </div>
        </div>
      </div>

      {/* Right panel — cream */}
      <div style={{
        flex: 1,
        background: "oklch(0.97 0.008 85)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 48px",
      }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 32 }}>
            <LangSwitcher />
          </div>

          <h1 style={{
            fontFamily: "Playfair Display, Georgia, serif", fontWeight: 800,
            fontSize: 28, color: "oklch(0.18 0.065 260)", marginBottom: 8,
          }}>
            {L.title}
          </h1>
          <p style={{ fontSize: 14, color: "oklch(0.55 0.03 260)", marginBottom: 36 }}>
            {L.subtitle}
          </p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "oklch(0.18 0.065 260)", letterSpacing: "0.05em", display: "block", marginBottom: 6 }}>
                {L.username}
              </label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="admin"
                required
                style={{
                  width: "100%", padding: "12px 16px",
                  border: "1.5px solid oklch(0.18 0.065 260 / 0.15)",
                  borderRadius: 8, fontSize: 14, fontFamily: "Inter, sans-serif",
                  background: "#fff", color: "oklch(0.18 0.065 260)",
                  outline: "none", transition: "border-color 0.2s",
                }}
                onFocus={e => e.target.style.borderColor = "oklch(0.77 0.18 68)"}
                onBlur={e => e.target.style.borderColor = "oklch(0.18 0.065 260 / 0.15)"}
              />
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "oklch(0.18 0.065 260)", letterSpacing: "0.05em", display: "block", marginBottom: 6 }}>
                {L.password}
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: "100%", padding: "12px 16px",
                  border: "1.5px solid oklch(0.18 0.065 260 / 0.15)",
                  borderRadius: 8, fontSize: 14, fontFamily: "Inter, sans-serif",
                  background: "#fff", color: "oklch(0.18 0.065 260)",
                  outline: "none", transition: "border-color 0.2s",
                }}
                onFocus={e => e.target.style.borderColor = "oklch(0.77 0.18 68)"}
                onBlur={e => e.target.style.borderColor = "oklch(0.18 0.065 260 / 0.15)"}
              />
            </div>

            {error && (
              <div style={{ padding: "10px 14px", background: "rgba(220,50,50,0.08)", border: "1px solid rgba(220,50,50,0.2)", borderRadius: 8, fontSize: 13, color: "#c0392b" }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%", padding: "13px",
                background: loading ? "oklch(0.85 0.1 68)" : "oklch(0.77 0.18 68)",
                color: "oklch(0.18 0.065 260)",
                border: "none", borderRadius: 8,
                fontSize: 14, fontWeight: 700, fontFamily: "Inter, sans-serif",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "opacity 0.2s", letterSpacing: "0.03em",
              }}
            >
              {loading ? L.loading : L.submit}
            </button>
          </form>

          <div style={{ marginTop: 32, paddingTop: 24, borderTop: "1px solid oklch(0.18 0.065 260 / 0.08)", textAlign: "center" }}>
            <a href="http://localhost:3001" style={{ fontSize: 13, color: "oklch(0.55 0.03 260)", textDecoration: "none" }}>
              {L.back}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
