"use client";
import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { LangSwitcher } from "@/components/lang-switcher";
import { useLang } from "@/contexts/lang";

const BG = "https://images.pexels.com/photos/29465759/pexels-photo-29465759.jpeg?auto=compress&cs=tinysrgb&w=1200&h=900";

export default function SignInPage() {
  const router = useRouter();
  const { t } = useLang();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading(true);
    setError("");
    const res = await signIn("credentials", { email: email.trim(), password, redirect: false });
    setLoading(false);
    if (res?.ok) { router.push("/me"); }
    else setError(res?.error === "CredentialsSignin" ? t.signin.error_credentials : t.signin.error_generic);
  }

  const inputStyle = { borderColor: "oklch(0.18 0.065 260 / 0.2)", background: "white", color: "var(--color-navy)" };
  const focusBorder = (e: React.FocusEvent<HTMLInputElement>) => (e.target.style.borderColor = "var(--color-gold)");
  const blurBorder  = (e: React.FocusEvent<HTMLInputElement>) => (e.target.style.borderColor = "oklch(0.18 0.065 260 / 0.2)");

  return (
    <div className="min-h-screen flex">
      {/* Left photo panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <img src={BG} alt="Tunisie" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0" style={{ background: "linear-gradient(135deg, oklch(0.18 0.065 260 / 0.72) 0%, oklch(0.60 0.22 27 / 0.45) 100%)" }} />
        <div className="relative z-10 flex flex-col justify-end p-12">
          <Link href="/" className="absolute top-8 left-8 text-2xl font-bold text-white"
                style={{ fontFamily: "var(--font-display)" }}>
            <span style={{ color: "var(--color-gold)" }}>Estate</span>Mind
          </Link>
          <blockquote className="text-white">
            <p className="text-2xl font-medium leading-snug mb-4" style={{ fontFamily: "var(--font-display)" }}>
              "{t.signin.tagline}"
            </p>
            <footer className="text-white/60 text-sm">{t.signin.brand_sub}</footer>
          </blockquote>
        </div>
      </div>

      {/* Right form panel */}
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
              {t.signin.title}
            </h1>
            <p className="text-sm" style={{ color: "var(--color-navy)", opacity: 0.55 }}>
              {t.signin.no_account}{" "}
              <Link href="/signup" className="font-semibold hover:underline" style={{ color: "var(--color-gold)" }}>
                {t.signin.create}
              </Link>
            </p>
          </div>

          {/* Demo hint */}
          <div className="mb-6 rounded-xl px-4 py-3 text-sm" style={{ background: "oklch(0.77 0.18 68 / 0.12)", color: "var(--color-navy)" }}>
            <span className="font-semibold">{t.signin.demo_label} :</span> demo@estatemind.local / demo-pass
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: "var(--color-navy)" }}>{t.signin.email}</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                     placeholder={t.signin.placeholder_email}
                     className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all"
                     style={inputStyle} onFocus={focusBorder} onBlur={blurBorder} />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: "var(--color-navy)" }}>{t.signin.password}</label>
              <div className="relative">
                <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} required
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
              {loading ? t.signin.loading : t.signin.submit}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
