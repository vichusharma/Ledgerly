"use client";

import { useState, useRef, useEffect } from "react";
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
  // Major national banks (default top 10)
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
  // Online & challenger banks
  "Boursorama Banque",
  "Hello bank!",
  "Fortuneo",
  "Monabanq",
  "N26",
  "Revolut",
  "Qonto",
  "Shine",
  "Sumeria",
  "Nickel",
  "Ma French Bank",
  "Blank",
  "Memo Bank",
  "Anytime",
  // Regional Crédit Agricole
  "Crédit Agricole Alpes Provence",
  "Crédit Agricole Alsace Vosges",
  "Crédit Agricole Aquitaine",
  "Crédit Agricole Atlantique Vendée",
  "Crédit Agricole Brie Picardie",
  "Crédit Agricole Bretagne",
  "Crédit Agricole Centre France",
  "Crédit Agricole Centre Loire",
  "Crédit Agricole Centre Ouest",
  "Crédit Agricole Centre-Est",
  "Crédit Agricole Charente-Maritime Deux-Sèvres",
  "Crédit Agricole Charente-Périgord",
  "Crédit Agricole Côtes d'Armor",
  "Crédit Agricole des Savoie",
  "Crédit Agricole du Finistère",
  "Crédit Agricole du Languedoc",
  "Crédit Agricole du Morbihan",
  "Crédit Agricole Franche-Comté",
  "Crédit Agricole Guadeloupe",
  "Crédit Agricole Île-de-France",
  "Crédit Agricole Ille-et-Vilaine",
  "Crédit Agricole Loire Haute-Loire",
  "Crédit Agricole Lorraine",
  "Crédit Agricole Martinique Guyane",
  "Crédit Agricole Nord Est",
  "Crédit Agricole Nord Midi-Pyrénées",
  "Crédit Agricole Nord de France",
  "Crédit Agricole Normandie",
  "Crédit Agricole Normandie Seine",
  "Crédit Agricole Provence Côte d'Azur",
  "Crédit Agricole Pyrénées Gascogne",
  "Crédit Agricole Réunion",
  "Crédit Agricole Sud Méditerranée",
  "Crédit Agricole Sud Rhône Alpes",
  "Crédit Agricole Toulouse 31",
  "Crédit Agricole Val de France",
  // Regional Banque Populaire
  "Banque Populaire Auvergne Rhône Alpes",
  "Banque Populaire Bourgogne Franche-Comté",
  "Banque Populaire Grand Ouest",
  "Banque Populaire Méditerranée",
  "Banque Populaire Nord",
  "Banque Populaire Occitane",
  "Banque Populaire Rives de Paris",
  "Banque Populaire Sud",
  "Banque Populaire Val de France",
  "BRED Banque Populaire",
  "CASDEN Banque Populaire",
  // Regional Caisse d'Épargne
  "Caisse d'Épargne Alsace",
  "Caisse d'Épargne Aquitaine Poitou-Charentes",
  "Caisse d'Épargne Auvergne et Limousin",
  "Caisse d'Épargne Bourgogne Franche-Comté",
  "Caisse d'Épargne Bretagne Pays de Loire",
  "Caisse d'Épargne Côte d'Azur",
  "Caisse d'Épargne Grand Est Europe",
  "Caisse d'Épargne Hauts de France",
  "Caisse d'Épargne Île-de-France",
  "Caisse d'Épargne Loire-Centre",
  "Caisse d'Épargne Loire Drôme Ardèche",
  "Caisse d'Épargne Midi-Pyrénées",
  "Caisse d'Épargne Normandie",
  "Caisse d'Épargne Provence-Alpes-Corse",
  "Caisse d'Épargne Rhône Alpes",
  // Regional Crédit Mutuel
  "Crédit Mutuel Arkéa",
  "Crédit Mutuel Bretagne",
  "Crédit Mutuel Centre Est Europe",
  "Crédit Mutuel du Sud Ouest",
  "Crédit Mutuel Loire-Atlantique et Centre Ouest",
  "Crédit Mutuel Maine-Anjou Basse-Normandie",
  "Crédit Mutuel Midi-Atlantique",
  "Crédit Mutuel Nord Europe",
  "Crédit Mutuel Normand",
  "Crédit Mutuel Océan",
  "Crédit Mutuel Savoie-Mont Blanc",
  // CIC regional
  "CIC Est",
  "CIC Lyonnaise de Banque",
  "CIC Nord Ouest",
  "CIC Ouest",
  "CIC Sud Ouest",
  // International banks with French branches
  "ABN AMRO France",
  "Barclays France",
  "BBVA France",
  "Citibank France",
  "Deutsche Bank France",
  "Goldman Sachs France",
  "ING France",
  "JPMorgan Chase France",
  "Morgan Stanley France",
  "Santander France",
  "UBS France",
  // Insurance-backed banks
  "AXA Banque",
  "Allianz Banque",
  "Groupama Banque",
  "MAAF Banque",
  "MIF Banque",
  // Cooperative & mutual
  "Crédit Coopératif",
  "Crédit Maritime Mutuel",
  "Banque Française Mutualiste",
  // Private & wealth management
  "Banque Delubac & Cie",
  "Banque Neuflize OBC",
  "Banque Palatine",
  "Banque Richelieu France",
  "Banque Transatlantique",
  "Edmond de Rothschild",
  "Lazard Frères Banque",
  "Milleis Banque",
  "Rothschild & Co",
  "Société Marseillaise de Crédit",
  // Consumer credit & auto finance
  "Cetelem",
  "Cofidis",
  "Floa Banque",
  "Franfinance",
  "My Money Bank",
  "PSA Banque France",
  "RCI Banque",
  "Sofinco",
  "Younited Credit",
  // Public & development
  "Bpifrance",
  "Caisse des Dépôts et Consignations",
  "Natixis",
  // Overseas
  "Banque des Antilles Françaises",
  "BNP Paribas Réunion",
  "Banque de la Réunion",
  "Crédit Agricole de la Réunion",
  "Société Générale Guadeloupe",
  "Société Générale Martinique",
];

function InstitutionCombobox({ value, onChange, placeholder, inputClass }: {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  inputClass: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const matches = value.trim() === ""
    ? FR_BANKS.slice(0, 10)
    : FR_BANKS.filter(b => b.toLowerCase().includes(value.toLowerCase())).slice(0, 10);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={e => { if (e.key === "Escape") setOpen(false); }}
        className={inputClass}
        placeholder={placeholder}
        autoComplete="off"
      />
      {open && matches.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-white dark:bg-secondary border border-surface-border dark:border-border rounded-lg shadow-lg overflow-hidden max-h-52 overflow-y-auto">
          {matches.map(bank => (
            <li key={bank}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-muted text-slate-800 dark:text-foreground"
                onMouseDown={e => {
                  e.preventDefault();
                  onChange(bank);
                  setOpen(false);
                }}
              >
                {bank}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

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
                <InstitutionCombobox
                  value={form.institution}
                  onChange={val => setForm(f => ({ ...f, institution: val }))}
                  placeholder={ax.institutionPlaceholder}
                  inputClass={inputClass}
                />
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
