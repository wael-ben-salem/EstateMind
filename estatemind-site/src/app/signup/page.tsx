"use client";
import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { LangSwitcher } from "@/components/lang-switcher";
import { useLang } from "@/contexts/lang";

const BG = "https://images.pexels.com/photos/32465895/pexels-photo-32465895.jpeg?auto=compress&cs=tinysrgb&w=1200&h=900";

export default function SignUpPage() {
  const router = useRouter();
  const { t } = useLang();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password || password.length < 6) {
      setError(t.signup.error_short_pw);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim() || undefined, email: email.trim(), password }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.error ?? t.signup.error_generic);
        setLoading(false);
        return;
      }
      await signIn("credentials", { email: email.trim(), password, redirect: false });
      router.push("/");
      router.refresh();
    } catch {
      setError(t.signup.error_unavailable);
      setLoading(false);
    }
  }

  const inputStyle = { borderColor: "oklch(0.18 0.065 260 / 0.2)", background: "white", color: "var(--color-navy)" };
  const focusBorder = (e: React.FocusEvent<HTMLInputElement>) => (e.target.style.borderColor = "var(--color-gold)");
  const blurBorder  = (e: React.FocusEvent<HTMLInputElement>) => (e.target.style.borderColor = "oklch(0.18 0.065 260 / 0.2)");

  const STATS = [
    { n: "49 835+", l: t.signup.stat_listings },
    { n: "6",       l: t.signup.stat_agents },
    { n: "92%",     l: t.signup.stat_accuracy },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Left photo panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <img src={BG} alt="Tunisie" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0" style={{ background: "linear-gradient(135deg, oklch(0.60 0.22 27 / 0.6) 0%, oklch(0.18 0.065 260 / 0.72) 100%)" }} />
        <div className="relative z-10 flex flex-col justify-end p-12">
          <Link href="/" className="absolute top-8 left-8 text-2xl font-bold text-white"
                style={{ fontFamily: "var(--font-display)" }}>
            <span style={{ color: "var(--color-gold)" }}>Estate</span>Mind
          </Link>
          <div className="text-white space-y-4">
            {STATS.map(({ n, l }) => (
              <div key={n} className="flex items-center gap-3">
                <span className="text-2xl font-bold" style={{ fontFamily: "var(--font-display)", color: "var(--color-gold)" }}>{n}</span>
                <span className="text-white/70 text-sm">{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12" style={{ background: "var(--color-cream)" }}>
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-between mb-8">
            <Link href="/">
              <img src="/logo.png" alt="EstateMind" style={{ height: "44px", width: "auto", objectFit: "contain" }} />
            </Link>
            <LangSwitcher />
          </div>
          {/* Desktop lang switcher */}
          <div className="hidden lg:flex justify-end mb-4">
            <LangSwitcher />
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: "var(--font-display)", color: "var(--color-navy)" }}>
              {t.signup.title}
            </h1>
            <p className="text-sm" style={{ color: "var(--color-navy)", opacity: 0.55 }}>
              {t.signup.has_account}{" "}
              <Link href="/signin" className="font-semibold hover:underline" style={{ color: "var(--color-gold)" }}>
                {t.signup.signin_link}
              </Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: "var(--color-navy)" }}>
                {t.signup.name} <span className="opacity-40">{t.signup.name_optional}</span>
              </label>
              <input type="text" value={name} onChange={e => setName(e.target.value)}
                     placeholder="Mohamed Trabelsi"
                     className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all"
                     style={inputStyle} onFocus={focusBorder} onBlur={blurBorder} />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: "var(--color-navy)" }}>{t.signup.email}</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                     placeholder={t.signup.placeholder_email}
                     className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all"
                     style={inputStyle} onFocus={focusBorder} onBlur={blurBorder} />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: "var(--color-navy)" }}>
                {t.signup.password} <span className="opacity-40">{t.signup.password_hint}</span>
              </label>
              <div className="relative">
                <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} required minLength={6}
                       placeholder="••••••••"
                       className="w-full px-4 py-3 pr-12 rounded-xl border text-sm outline-none transition-all"
                       style={inputStyle} onFocus={focusBorder} onBlur={blurBorder} />
                <button type="button" onClick={() => setShowPw(s => !s)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                        style={{ color: "var(--color-navy)", opacity: 0.4 }}>
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && <p className="text-sm font-medium" style={{ color: "var(--color-terra)" }}>{error}</p>}

            <button type="submit" disabled={loading}
                    className="w-full py-3.5 rounded-xl font-bold text-sm transition-all hover:opacity-90 disabled:opacity-60 flex items-center justify-center gap-2 mt-2"
                    style={{ background: "var(--color-navy)", color: "white" }}>
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? t.signup.loading : t.signup.submit}
            </button>

            <p className="text-xs text-center mt-3" style={{ color: "var(--color-navy)", opacity: 0.4 }}>
              {t.signup.terms}
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
