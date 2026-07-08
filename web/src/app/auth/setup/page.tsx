"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStatus, useSetupPassword, useLogin } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";

export default function SetupPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const sx = t("setup");
  const lx = t("login");

  const { data: status, isLoading: statusLoading } = useAuthStatus();
  const setupPassword = useSetupPassword();
  const login = useLogin();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (status?.initialized) {
      router.replace("/auth/login");
    }
  }, [status, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError(sx.tooShort);
      return;
    }
    if (password !== confirm) {
      setError(sx.mismatch);
      return;
    }

    try {
      await setupPassword.mutateAsync(password);
      await login.mutateAsync(password);
      router.push("/dashboard");
    } catch (err: any) {
      if (err?.response?.status === 409) {
        router.replace("/auth/login");
      } else {
        setError(sx.errorGeneric);
      }
    }
  };

  if (statusLoading || status?.initialized) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const isPending = setupPassword.isPending || login.isPending;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/ledgerly-mark.svg" alt="Ledgerly" className="w-12 h-12 mx-auto mb-3" />
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">Ledgerly</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-1">{sx.subtitle}</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white dark:bg-card rounded-2xl border border-surface-border dark:border-border p-6 space-y-4"
        >
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-muted-foreground">
              {sx.passwordLabel}
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoFocus
              required
              minLength={8}
              className="mt-1 w-full text-sm border border-surface-border dark:border-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand/30 bg-white dark:bg-secondary dark:text-foreground"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-muted-foreground">
              {sx.confirmLabel}
            </label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              required
              minLength={8}
              className="mt-1 w-full text-sm border border-surface-border dark:border-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand/30 bg-white dark:bg-secondary dark:text-foreground"
              placeholder="••••••••"
            />
          </div>

          {error && <p className="text-xs text-danger">{error}</p>}

          <button
            type="submit"
            disabled={isPending || !password || !confirm}
            className="w-full bg-brand text-white font-medium py-3 rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {isPending ? sx.submitting : sx.submit}
          </button>
        </form>

        <p className="text-xs text-center text-slate-400 dark:text-muted-foreground mt-4">
          {lx.privacy}
        </p>
      </div>
    </div>
  );
}
