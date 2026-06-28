"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAccounts, usePersons, useCreateAccount } from "@/lib/api/hooks";
import { formatMoney } from "@/lib/format/money";
import { Wallet, Archive } from "lucide-react";

const ACCOUNT_TYPES = [
  { value: "bank", label: "Compte bancaire" },
  { value: "savings", label: "Épargne" },
  { value: "investment_wrapper", label: "Enveloppe d'investissement" },
  { value: "liability", label: "Crédit / Passif" },
];

const WRAPPER_TYPES = [
  "PEA", "PEA_PME", "AV", "PER", "PERO", "PERCO", "PEE",
  "CTO", "LIVRET_A", "LDDS", "LEP", "ESOP", "OTHER",
];

export default function AccountsPage() {
  const { data: accounts = [] } = useAccounts("household", false);
  const { data: persons = [] } = usePersons();
  const createAccount = useCreateAccount();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", type: "bank", wrapper_type: "", institution: "",
    currency: "EUR", owner_id: "", ownership_pct: "100",
  });

  const handleCreate = async () => {
    await createAccount.mutateAsync({
      ...form,
      wrapper_type: form.wrapper_type || null,
      owner_id: Number(form.owner_id),
      ownership_pct: parseFloat(form.ownership_pct),
    });
    setShowForm(false);
  };

  const groupByType = accounts.reduce((acc: Record<string, any[]>, a: any) => {
    const t = a.type;
    if (!acc[t]) acc[t] = [];
    acc[t].push(a);
    return acc;
  }, {});

  return (
    <AppShell>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-900">Comptes</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700"
          >
            + Compte
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="bg-white rounded-xl border border-surface-border p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Nouveau compte</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="text-xs text-slate-500">Nom du compte</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
                  placeholder="PEA Boursorama"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500">Type</label>
                <select
                  value={form.type}
                  onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none"
                >
                  {ACCOUNT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {form.type === "investment_wrapper" && (
                <div>
                  <label className="text-xs text-slate-500">Enveloppe</label>
                  <select
                    value={form.wrapper_type}
                    onChange={e => setForm(f => ({ ...f, wrapper_type: e.target.value }))}
                    className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none"
                  >
                    <option value="">Sélectionner</option>
                    {WRAPPER_TYPES.map(w => <option key={w} value={w}>{w}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label className="text-xs text-slate-500">Établissement</label>
                <input
                  value={form.institution}
                  onChange={e => setForm(f => ({ ...f, institution: e.target.value }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
                  placeholder="BNP Paribas"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500">Titulaire</label>
                <select
                  value={form.owner_id}
                  onChange={e => setForm(f => ({ ...f, owner_id: e.target.value }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none"
                >
                  <option value="">Sélectionner</option>
                  {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-500">% de propriété</label>
                <input
                  type="number"
                  value={form.ownership_pct}
                  onChange={e => setForm(f => ({ ...f, ownership_pct: e.target.value }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 money focus:outline-none focus:ring-2 focus:ring-brand/20"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!form.name || !form.owner_id}
                className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
              >
                Créer
              </button>
              <button onClick={() => setShowForm(false)} className="text-slate-500 text-sm px-4 py-2 rounded-lg hover:bg-slate-100">
                Annuler
              </button>
            </div>
          </div>
        )}

        {/* Account groups */}
        {ACCOUNT_TYPES.map(({ value, label }) => {
          const accs = groupByType[value] || [];
          if (accs.length === 0) return null;
          return (
            <div key={value}>
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{label}</h2>
              <div className="space-y-2">
                {accs.map((a: any) => {
                  const owner = persons.find((p: any) => p.id === a.owner_id);
                  return (
                    <div key={a.id} className="bg-white rounded-xl border border-surface-border p-4 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                        <Wallet className="h-4 w-4 text-slate-500" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">{a.name}</p>
                        <p className="text-xs text-slate-400">
                          {a.institution || "—"} · {owner?.name || "—"}
                          {a.wrapper_type ? ` · ${a.wrapper_type}` : ""}
                          {a.ownership_pct !== 100 ? ` · ${a.ownership_pct}%` : ""}
                        </p>
                      </div>
                      <span className="text-xs text-slate-400">{a.currency}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {accounts.length === 0 && (
          <div className="text-center py-12 text-slate-400 text-sm">
            Aucun compte — créez-en un pour commencer
          </div>
        )}
      </div>
    </AppShell>
  );
}
