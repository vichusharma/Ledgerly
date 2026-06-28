"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAccounts, usePersons, useCreateAccount } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney } from "@/lib/format/money";
import { Wallet } from "lucide-react";

const WRAPPER_TYPES = [
  "PEA", "PEA_PME", "AV", "PER", "PERO", "PERCO", "PEE",
  "CTO", "LIVRET_A", "LDDS", "LEP", "ESOP", "OTHER",
];

const FR_BANKS = [
  "BNP Paribas",
  "Crédit Agricole",
  "Société Générale",
  "Caisse d'Épargne",
  "Banque Populaire",
  "Crédit Mutuel",
  "LCL",
  "La Banque Postale",
  "CIC",
  "HSBC France",
  "Boursorama Banque",
  "Hello bank!",
  "Fortuneo",
  "Monabanq",
  "N26",
  "Revolut",
  "Qonto",
  "Shine",
  "Sumeria",
  "Arkéa",
];

export default function AccountsPage() {
  const { data: accounts = [] } = useAccounts("household", false);
  const { data: persons = [] } = usePersons();
  const createAccount = useCreateAccount();
  const { t } = useLanguage();
  const ax = t("accounts");

  const ACCOUNT_TYPES = [
    { value: "bank",               label: ax.types.bank },
    { value: "savings",            label: ax.types.savings },
    { value: "investment_wrapper", label: ax.types.investment_wrapper },
    { value: "liability",          label: ax.types.liability },
  ];

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
    const tp = a.type;
    if (!acc[tp]) acc[tp] = [];
    acc[tp].push(a);
    return acc;
  }, {});

  const selectClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none bg-white dark:bg-secondary dark:text-foreground";
  const inputClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";

  return (
    <AppShell>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{ax.title}</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700"
          >
            {ax.add}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{ax.newAccount}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.name}</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className={inputClass}
                  placeholder={ax.namePlaceholder}
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.type}</label>
                <select
                  value={form.type}
                  onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                  className={selectClass}
                >
                  {ACCOUNT_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label}</option>)}
                </select>
              </div>
              {form.type === "investment_wrapper" && (
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.wrapper}</label>
                  <select
                    value={form.wrapper_type}
                    onChange={e => setForm(f => ({ ...f, wrapper_type: e.target.value }))}
                    className={selectClass}
                  >
                    <option value="">{ax.select}</option>
                    {WRAPPER_TYPES.map(w => <option key={w} value={w}>{w}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.institution}</label>
                <input
                  value={form.institution}
                  onChange={e => setForm(f => ({ ...f, institution: e.target.value }))}
                  className={inputClass}
                  placeholder={ax.institutionPlaceholder}
                  list="fr-banks"
                  autoComplete="off"
                />
                <datalist id="fr-banks">
                  {FR_BANKS.map(bank => <option key={bank} value={bank} />)}
                </datalist>
              </div>
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.owner}</label>
                <select
                  value={form.owner_id}
                  onChange={e => setForm(f => ({ ...f, owner_id: e.target.value }))}
                  className={selectClass}
                >
                  <option value="">{ax.select}</option>
                  {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.ownershipPct}</label>
                <input
                  type="number"
                  value={form.ownership_pct}
                  onChange={e => setForm(f => ({ ...f, ownership_pct: e.target.value }))}
                  className={`${inputClass} money`}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!form.name || !form.owner_id}
                className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
              >
                {ax.create}
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
              >
                {ax.cancel}
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
              <h2 className="text-xs font-semibold text-slate-400 dark:text-muted-foreground uppercase tracking-wider mb-2">{label}</h2>
              <div className="space-y-2">
                {accs.map((a: any) => {
                  const owner = persons.find((p: any) => p.id === a.owner_id);
                  return (
                    <div key={a.id} className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-secondary flex items-center justify-center">
                        <Wallet className="h-4 w-4 text-slate-500 dark:text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800 dark:text-foreground">{a.name}</p>
                        <p className="text-xs text-slate-400 dark:text-muted-foreground">
                          {a.institution || "—"} · {owner?.name || "—"}
                          {a.wrapper_type ? ` · ${a.wrapper_type}` : ""}
                          {a.ownership_pct !== 100 ? ` · ${a.ownership_pct}%` : ""}
                        </p>
                      </div>
                      <span className="text-xs text-slate-400 dark:text-muted-foreground">{a.currency}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {accounts.length === 0 && (
          <div className="text-center py-12 text-slate-400 dark:text-muted-foreground text-sm">
            {ax.noAccounts}
          </div>
        )}
      </div>
    </AppShell>
  );
}
