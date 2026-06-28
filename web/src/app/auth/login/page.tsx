"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLogin } from "@/lib/api/hooks";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const login = useLogin();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login.mutateAsync(password);
      router.push("/dashboard");
    } catch {
      setError("Mot de passe incorrect");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-brand flex items-center justify-center text-white font-bold text-xl mx-auto mb-3">
            L
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Ledgerly</h1>
          <p className="text-sm text-slate-500 mt-1">Finances familiales · Local & privé</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-surface-border p-6 space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-600">Mot de passe du foyer</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoFocus
              required
              className="mt-1 w-full text-sm border border-surface-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand/30"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-xs text-danger">{error}</p>
          )}

          <button
            type="submit"
            disabled={login.isPending || !password}
            className="w-full bg-brand text-white font-medium py-3 rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {login.isPending ? "Connexion…" : "Se connecter"}
          </button>
        </form>

        <p className="text-xs text-center text-slate-400 mt-4">
          Toutes les données restent sur votre machine.
        </p>
      </div>
    </div>
  );
}
