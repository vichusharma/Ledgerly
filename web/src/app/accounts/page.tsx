"use client";

import React, { useState, createContext, useContext } from "react";
import { AppShell } from "@/components/AppShell";
import { useAccounts, usePersons, useCreateAccount, useUpdateAccount, useArchiveAccount } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney } from "@/lib/format/money";
import { Wallet, Pencil, Trash2, Users } from "lucide-react";
import { InstitutionCombobox } from "@/components/InstitutionCombobox";

const WRAPPER_TYPES = [
  "PEA", "PEA_PME", "AV", "PER", "PERO", "PERCO", "PEE",
  "CTO", "LIVRET_A", "LDDS", "LEP", "ESOP", "OTHER",
];

// Regulated savings books — shown as the "product" selector for type === "savings".
const SAVINGS_PRODUCTS = ["LIVRET_A", "LDDS", "LEP", "OTHER"];

// Which account types expose a wrapper/product selector, and the options for each.
const showsWrapper = (type: string) => type === "investment_wrapper" || type === "savings";
const wrapperOptionsFor = (type: string) =>
  type === "savings" ? SAVINGS_PRODUCTS : WRAPPER_TYPES;

const BLANK_FORM = {
  name: "", type: "bank", wrapper_type: "", institution: "",
  currency: "EUR", owner_id: "", joint_owner_id: "", ownership_pct: "100",
};

const PAGE_SIZE = 8;

const AVATAR_COLORS = [
  "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300",
  "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
];

const TYPE_BADGE: Record<string, string> = {
  bank:               "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  savings:            "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  investment_wrapper: "bg-violet-50 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
  liability:          "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300",
};

function interp(tpl: string, vars: Record<string, string | number>) {
  return tpl.replace(/\{\{(\w+)\}\}/g, (_, k) => String(vars[k] ?? ""));
}

function initials(name: string) {
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

// ── Shared context so module-level components can access page state ──────────
type Ctx = {
  accounts: any[];
  persons: any[];
  soloAccounts: any[];
  jointAccounts: any[];
  panelFilter: Record<string, string>;
  setPanelFilter: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  expanded: Record<string, boolean>;
  setExpanded: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  ax: any;
  ACCOUNT_TYPES: { value: string; label: string }[];
  inputClass: string;
  selectClass: string;
  thClass: string;
  tdClass: string;
  editingId: number | null;
  archiveConfirmId: number | null;
  editForm: typeof BLANK_FORM;
  setEditForm: React.Dispatch<React.SetStateAction<typeof BLANK_FORM>>;
  startEdit: (a: any) => void;
  handleSave: (id: number) => Promise<void>;
  handleArchive: (id: number) => Promise<void>;
  setEditingId: React.Dispatch<React.SetStateAction<number | null>>;
  setArchiveConfirmId: React.Dispatch<React.SetStateAction<number | null>>;
  setForm: React.Dispatch<React.SetStateAction<typeof BLANK_FORM>>;
  setShowForm: React.Dispatch<React.SetStateAction<boolean>>;
};

const AccountCtx = createContext<Ctx | null>(null);
const useAcc = () => useContext(AccountCtx)!;

// ── EditRow ──────────────────────────────────────────────────────────────────
function EditRow({ a, colSpan }: { a: any; colSpan: number }) {
  const { ax, ACCOUNT_TYPES, editForm, setEditForm, handleSave, setEditingId, persons, inputClass, selectClass } = useAcc();
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-4 border-t border-brand/30 dark:border-brand/20 bg-blue-50/40 dark:bg-blue-950/10">
        <div className="grid grid-cols-2 gap-3 max-w-2xl">
          <div className="col-span-2">
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.name}</label>
            <input value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.type}</label>
            <select
              value={editForm.type}
              onChange={e => setEditForm(f => ({
                ...f,
                type: e.target.value,
                // Drop a product/wrapper value that no longer applies to the new type.
                wrapper_type: showsWrapper(e.target.value) ? f.wrapper_type : "",
              }))}
              className={selectClass}
            >
              {ACCOUNT_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.institution}</label>
            <InstitutionCombobox value={editForm.institution} onChange={val => setEditForm(f => ({ ...f, institution: val }))} placeholder={ax.institutionPlaceholder} inputClass={inputClass} />
          </div>
          {showsWrapper(editForm.type) && (
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{editForm.type === "savings" ? ax.product : ax.wrapper}</label>
              <select value={editForm.wrapper_type} onChange={e => setEditForm(f => ({ ...f, wrapper_type: e.target.value }))} className={selectClass}>
                <option value="">{ax.select}</option>
                {wrapperOptionsFor(editForm.type).map(w => <option key={w} value={w}>{w}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.owner}</label>
            <select value={editForm.owner_id} onChange={e => setEditForm(f => ({ ...f, owner_id: e.target.value, joint_owner_id: e.target.value === f.joint_owner_id ? "" : f.joint_owner_id }))} className={selectClass}>
              <option value="">{ax.select}</option>
              {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.jointOwner}</label>
            <select value={editForm.joint_owner_id} onChange={e => setEditForm(f => ({ ...f, joint_owner_id: e.target.value }))} className={selectClass}>
              <option value="">{ax.none}</option>
              {persons.filter((p: any) => !editForm.owner_id || String(p.id) !== editForm.owner_id).map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.ownershipPct}</label>
            <input type="number" min={1} max={100} value={editForm.ownership_pct} onChange={e => setEditForm(f => ({ ...f, ownership_pct: e.target.value }))} className={`${inputClass} money`} />
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={() => handleSave(a.id)} disabled={!editForm.name || !editForm.owner_id} className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700">
            {ax.save}
          </button>
          <button onClick={() => setEditingId(null)} className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
            {ax.cancel}
          </button>
        </div>
      </td>
    </tr>
  );
}

// ── ArchiveRow ───────────────────────────────────────────────────────────────
function ArchiveRow({ a, colSpan }: { a: any; colSpan: number }) {
  const { ax, handleArchive, setArchiveConfirmId } = useAcc();
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-3 border-t border-red-200 dark:border-red-900/30 bg-red-50/50 dark:bg-red-950/10">
        <div className="flex items-center gap-3">
          <p className="text-xs text-slate-600 dark:text-muted-foreground flex-1">
            <span className="font-medium">{ax.archiveConfirm}</span>{" "}
            <span className="text-slate-400">{ax.archiveHint}</span>
          </p>
          <button onClick={() => handleArchive(a.id)} className="text-xs font-medium text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg">
            {ax.archive}
          </button>
          <button onClick={() => setArchiveConfirmId(null)} className="text-xs text-slate-500 dark:text-muted-foreground px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
            {ax.cancel}
          </button>
        </div>
      </td>
    </tr>
  );
}

// ── AccountRow ───────────────────────────────────────────────────────────────
function AccountRow({ a, colSpan, showOwners = false }: { a: any; colSpan: number; showOwners?: boolean }) {
  const { persons, ACCOUNT_TYPES, ax, tdClass, editingId, archiveConfirmId, startEdit, setArchiveConfirmId, setEditingId } = useAcc();
  const owner = persons.find((p: any) => p.id === a.owner_id);
  const joint = a.joint_owner_id ? persons.find((p: any) => p.id === a.joint_owner_id) : null;
  const typeLabel = ACCOUNT_TYPES.find(t => t.value === a.type)?.label ?? a.type;
  const badgeCls = TYPE_BADGE[a.type] ?? "bg-slate-100 text-slate-600";
  return (
    <>
      <tr className="group hover:bg-slate-50 dark:hover:bg-secondary/30 transition-colors">
        <td className={tdClass}><span className="font-medium">{a.name}</span></td>
        <td className={tdClass}>
          <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-md ${badgeCls}`}>{typeLabel}</span>
        </td>
        <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>{a.institution || "—"}</td>
        {showOwners ? (
          <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>
            {owner?.name || "—"}{joint ? ` · ${joint.name}` : ""}
            {Number(a.ownership_pct) !== 100 ? ` (${a.ownership_pct}%)` : ""}
          </td>
        ) : (
          <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>{a.wrapper_type || "—"}</td>
        )}
        {!showOwners && (
          <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>
            {Number(a.ownership_pct) !== 100 ? `${a.ownership_pct}%` : "100%"}
          </td>
        )}
        <td className={tdClass}>
          <div className="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
            <button onClick={() => startEdit(a)} title={ax.edit} className="p-1.5 rounded-lg text-slate-400 hover:text-brand hover:bg-slate-100 dark:hover:bg-secondary transition-colors">
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button onClick={() => { setArchiveConfirmId(a.id); setEditingId(null); }} title={ax.archive} className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </td>
      </tr>
      {editingId === a.id && <EditRow a={a} colSpan={colSpan} />}
      {archiveConfirmId === a.id && editingId !== a.id && <ArchiveRow a={a} colSpan={colSpan} />}
    </>
  );
}

// ── MemberPanel ──────────────────────────────────────────────────────────────
function MemberPanel({ person, idx }: { person: any; idx: number }) {
  const { soloAccounts, panelFilter, setPanelFilter, ax, ACCOUNT_TYPES, thClass, setForm, setShowForm } = useAcc();
  const all = soloAccounts.filter((a: any) => a.owner_id === person.id);
  if (all.length === 0) return null;
  const filterKey = String(person.id);
  const activeFilter = panelFilter[filterKey] ?? "all";
  const presentTypes = Array.from(new Set(all.map((a: any) => a.type))) as string[];
  const visible = activeFilter === "all" ? all : all.filter((a: any) => a.type === activeFilter);
  const avatarCls = AVATAR_COLORS[idx % AVATAR_COLORS.length];
  const countLabel = interp(ax.accountsCount, { n: all.length, s: all.length !== 1 ? "s" : "" });

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-border dark:border-border">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold ${avatarCls}`}>
          {initials(person.name)}
        </div>
        <span className="text-sm font-semibold text-slate-800 dark:text-foreground">{person.name}</span>
        <span className="text-xs text-slate-400 dark:text-muted-foreground ml-1">{countLabel}</span>
        <button
          onClick={() => { setForm(f => ({ ...f, owner_id: String(person.id) })); setShowForm(true); }}
          className="ml-auto text-xs text-brand border border-brand/30 hover:bg-brand/5 px-3 py-1 rounded-lg transition-colors"
        >
          {ax.add}
        </button>
      </div>
      {presentTypes.length > 1 && (
        <div className="flex border-b border-surface-border dark:border-border bg-slate-50 dark:bg-secondary/30 px-3 pt-1">
          {["all", ...presentTypes].map(tp => {
            const label = tp === "all"
              ? interp(ax.allFilter, { n: all.length })
              : ACCOUNT_TYPES.find(t => t.value === tp)?.label ?? tp;
            return (
              <button
                key={tp}
                onClick={() => setPanelFilter(f => ({ ...f, [filterKey]: tp }))}
                className={`text-xs px-3 py-2 border-b-2 transition-colors ${
                  activeFilter === tp
                    ? "border-brand text-brand font-medium"
                    : "border-transparent text-slate-400 dark:text-muted-foreground hover:text-slate-600"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className={thClass} style={{ width: "30%" }}>{ax.name}</th>
            <th className={thClass} style={{ width: "16%" }}>{ax.type}</th>
            <th className={thClass} style={{ width: "20%" }}>{ax.institution}</th>
            <th className={thClass} style={{ width: "12%" }}>{ax.wrapper}</th>
            <th className={thClass} style={{ width: "10%" }}>{ax.ownershipPct}</th>
            <th className={thClass} style={{ width: "12%" }}></th>
          </tr>
        </thead>
        <tbody>
          {visible.map((a: any) => <AccountRow key={a.id} a={a} colSpan={6} />)}
        </tbody>
      </table>
    </div>
  );
}

// ── SharedPanel ──────────────────────────────────────────────────────────────
function SharedPanel() {
  const { jointAccounts, ax, thClass } = useAcc();
  if (jointAccounts.length === 0) return null;
  const countLabel = interp(ax.accountsCount, { n: jointAccounts.length, s: jointAccounts.length !== 1 ? "s" : "" });
  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-border dark:border-border">
        <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
          <Users className="h-4 w-4 text-amber-600 dark:text-amber-400" />
        </div>
        <span className="text-sm font-semibold text-slate-800 dark:text-foreground">{ax.shared}</span>
        <span className="text-xs text-slate-400 dark:text-muted-foreground ml-1">{countLabel}</span>
      </div>
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className={thClass} style={{ width: "28%" }}>{ax.name}</th>
            <th className={thClass} style={{ width: "15%" }}>{ax.type}</th>
            <th className={thClass} style={{ width: "18%" }}>{ax.institution}</th>
            <th className={thClass} style={{ width: "25%" }}>{ax.owners}</th>
            <th className={thClass} style={{ width: "14%" }}></th>
          </tr>
        </thead>
        <tbody>
          {jointAccounts.map((a: any) => <AccountRow key={a.id} a={a} colSpan={5} showOwners />)}
        </tbody>
      </table>
    </div>
  );
}

// ── ByTypeView ───────────────────────────────────────────────────────────────
function ByTypeView() {
  const { accounts, persons, ACCOUNT_TYPES, ax, thClass, tdClass, editingId, archiveConfirmId, startEdit, setArchiveConfirmId, setEditingId, expanded, setExpanded } = useAcc();
  const groupByType = accounts.reduce((acc: Record<string, any[]>, a: any) => {
    if (!acc[a.type]) acc[a.type] = [];
    acc[a.type].push(a);
    return acc;
  }, {});

  return (
    <>
      {ACCOUNT_TYPES.map(({ value, label }) => {
        const accs = groupByType[value] || [];
        if (accs.length === 0) return null;
        const isExpanded = expanded[value];
        const visible = isExpanded ? accs : accs.slice(0, PAGE_SIZE);
        const remaining = accs.length - PAGE_SIZE;
        const badgeCls = TYPE_BADGE[value] ?? "bg-slate-100 text-slate-600";
        return (
          <div key={value} className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-surface-border dark:border-border">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${badgeCls}`}>{label}</span>
              <span className="text-xs text-slate-400 dark:text-muted-foreground">({accs.length})</span>
            </div>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={thClass} style={{ width: "30%" }}>{ax.name}</th>
                  <th className={thClass} style={{ width: "18%" }}>{ax.institution}</th>
                  <th className={thClass} style={{ width: "14%" }}>{ax.owner}</th>
                  <th className={thClass} style={{ width: "12%" }}>{ax.wrapper}</th>
                  <th className={thClass} style={{ width: "12%" }}>{ax.ownershipPct}</th>
                  <th className={thClass} style={{ width: "14%" }}></th>
                </tr>
              </thead>
              <tbody>
                {visible.map((a: any) => {
                  const owner = persons.find((p: any) => p.id === a.owner_id);
                  const joint = a.joint_owner_id ? persons.find((p: any) => p.id === a.joint_owner_id) : null;
                  return (
                    <React.Fragment key={a.id}>
                      <tr className="group hover:bg-slate-50 dark:hover:bg-secondary/30 transition-colors">
                        <td className={tdClass}><span className="font-medium">{a.name}</span></td>
                        <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>{a.institution || "—"}</td>
                        <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>
                          {owner?.name || "—"}{joint ? ` + ${joint.name}` : ""}
                        </td>
                        <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>{a.wrapper_type || "—"}</td>
                        <td className={`${tdClass} text-slate-500 dark:text-muted-foreground`}>{a.ownership_pct}%</td>
                        <td className={tdClass}>
                          <div className="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => startEdit(a)} title={ax.edit} className="p-1.5 rounded-lg text-slate-400 hover:text-brand hover:bg-slate-100 dark:hover:bg-secondary transition-colors">
                              <Pencil className="h-3.5 w-3.5" />
                            </button>
                            <button onClick={() => { setArchiveConfirmId(a.id); setEditingId(null); }} title={ax.archive} className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors">
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                      {editingId === a.id && <EditRow a={a} colSpan={6} />}
                      {archiveConfirmId === a.id && editingId !== a.id && <ArchiveRow a={a} colSpan={6} />}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
            {accs.length > PAGE_SIZE && (
              <div className="px-4 py-2 border-t border-surface-border dark:border-border">
                <button onClick={() => setExpanded(e => ({ ...e, [value]: !isExpanded }))} className="text-xs text-brand hover:underline">
                  {isExpanded ? ax.showLess : interp(ax.showMore, { n: remaining })}
                </button>
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function AccountsPage() {
  const { data: accounts = [] } = useAccounts("household", false);
  const { data: persons = [] } = usePersons();
  const createAccount = useCreateAccount();
  const updateAccount = useUpdateAccount();
  const archiveAccount = useArchiveAccount();
  const { t } = useLanguage();
  const ax = t("accounts");

  const ACCOUNT_TYPES = [
    { value: "bank",               label: ax.types.bank },
    { value: "savings",            label: ax.types.savings },
    { value: "investment_wrapper", label: ax.types.investment_wrapper },
    { value: "liability",          label: ax.types.liability },
  ];

  const [viewMode, setViewMode] = useState<"member" | "type">("member");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(BLANK_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(BLANK_FORM);
  const [archiveConfirmId, setArchiveConfirmId] = useState<number | null>(null);
  const [panelFilter, setPanelFilter] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const handleCreate = async () => {
    await createAccount.mutateAsync({
      ...form,
      wrapper_type: form.wrapper_type || null,
      owner_id: Number(form.owner_id),
      joint_owner_id: form.joint_owner_id ? Number(form.joint_owner_id) : null,
      ownership_pct: parseFloat(form.ownership_pct),
    });
    setForm(BLANK_FORM);
    setShowForm(false);
  };

  const startEdit = (a: any) => {
    setEditForm({
      name: a.name, type: a.type,
      wrapper_type: a.wrapper_type || "",
      institution: a.institution || "",
      currency: a.currency,
      owner_id: String(a.owner_id),
      joint_owner_id: a.joint_owner_id ? String(a.joint_owner_id) : "",
      ownership_pct: String(a.ownership_pct),
    });
    setEditingId(a.id);
    setArchiveConfirmId(null);
  };

  const handleSave = async (id: number) => {
    await updateAccount.mutateAsync({
      id,
      name: editForm.name,
      type: editForm.type,
      institution: editForm.institution || null,
      owner_id: Number(editForm.owner_id),
      joint_owner_id: editForm.joint_owner_id ? Number(editForm.joint_owner_id) : null,
      wrapper_type: editForm.wrapper_type || null,
      ownership_pct: parseFloat(editForm.ownership_pct),
    });
    setEditingId(null);
  };

  const handleArchive = async (id: number) => {
    await archiveAccount.mutateAsync(id);
    setArchiveConfirmId(null);
  };

  const jointAccounts = accounts.filter((a: any) => a.joint_owner_id !== null);
  const soloAccounts  = accounts.filter((a: any) => a.joint_owner_id === null);

  const inputClass  = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const selectClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none bg-white dark:bg-secondary dark:text-foreground";
  const thClass     = "px-4 py-2.5 text-left text-xs font-medium text-slate-400 dark:text-muted-foreground uppercase tracking-wider bg-slate-50 dark:bg-secondary/50";
  const tdClass     = "px-4 py-3 text-sm text-slate-700 dark:text-foreground border-t border-surface-border dark:border-border";

  const ctx: Ctx = {
    accounts, persons, soloAccounts, jointAccounts,
    panelFilter, setPanelFilter, expanded, setExpanded,
    ax, ACCOUNT_TYPES, inputClass, selectClass, thClass, tdClass,
    editingId, archiveConfirmId, editForm, setEditForm,
    startEdit, handleSave, handleArchive, setEditingId, setArchiveConfirmId,
    setForm, setShowForm,
  };

  return (
    <AccountCtx.Provider value={ctx}>
      <AppShell>
        <div className="p-6 max-w-4xl mx-auto space-y-4">

          {/* Header */}
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{ax.title}</h1>
            <div className="flex items-center gap-3">
              <div className="flex items-center border border-surface-border dark:border-border rounded-lg overflow-hidden text-sm">
                <button
                  onClick={() => setViewMode("member")}
                  className={`px-3 py-1.5 transition-colors ${viewMode === "member" ? "bg-brand text-white font-medium" : "text-slate-500 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"}`}
                >
                  {ax.byMember}
                </button>
                <button
                  onClick={() => setViewMode("type")}
                  className={`px-3 py-1.5 transition-colors ${viewMode === "type" ? "bg-brand text-white font-medium" : "text-slate-500 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"}`}
                >
                  {ax.byType}
                </button>
              </div>
              <button onClick={() => { setForm(BLANK_FORM); setShowForm(s => !s); }} className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700">
                {ax.add}
              </button>
            </div>
          </div>

          {/* Create form */}
          {showForm && (
            <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5 space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{ax.newAccount}</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.name}</label>
                  <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputClass} placeholder={ax.namePlaceholder} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.type}</label>
                  <select
                    value={form.type}
                    onChange={e => setForm(f => ({
                      ...f,
                      type: e.target.value,
                      wrapper_type: showsWrapper(e.target.value) ? f.wrapper_type : "",
                    }))}
                    className={selectClass}
                  >
                    {ACCOUNT_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label}</option>)}
                  </select>
                </div>
                {showsWrapper(form.type) && (
                  <div>
                    <label className="text-xs text-slate-500 dark:text-muted-foreground">{form.type === "savings" ? ax.product : ax.wrapper}</label>
                    <select value={form.wrapper_type} onChange={e => setForm(f => ({ ...f, wrapper_type: e.target.value }))} className={selectClass}>
                      <option value="">{ax.select}</option>
                      {wrapperOptionsFor(form.type).map(w => <option key={w} value={w}>{w}</option>)}
                    </select>
                  </div>
                )}
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.institution}</label>
                  <InstitutionCombobox value={form.institution} onChange={val => setForm(f => ({ ...f, institution: val }))} placeholder={ax.institutionPlaceholder} inputClass={inputClass} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.owner}</label>
                  <select value={form.owner_id} onChange={e => setForm(f => ({ ...f, owner_id: e.target.value, joint_owner_id: e.target.value === f.joint_owner_id ? "" : f.joint_owner_id }))} className={selectClass}>
                    <option value="">{ax.select}</option>
                    {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.jointOwner}</label>
                  <select value={form.joint_owner_id} onChange={e => setForm(f => ({ ...f, joint_owner_id: e.target.value }))} className={selectClass}>
                    <option value="">{ax.none}</option>
                    {persons.filter((p: any) => !form.owner_id || String(p.id) !== form.owner_id).map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 dark:text-muted-foreground">{ax.ownershipPct}</label>
                  <input type="number" min={1} max={100} value={form.ownership_pct} onChange={e => setForm(f => ({ ...f, ownership_pct: e.target.value }))} className={`${inputClass} money`} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleCreate} disabled={!form.name || !form.owner_id} className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700">
                  {ax.create}
                </button>
                <button onClick={() => setShowForm(false)} className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
                  {ax.cancel}
                </button>
              </div>
            </div>
          )}

          {/* Views */}
          {accounts.length === 0 ? (
            <div className="text-center py-16 text-slate-400 dark:text-muted-foreground text-sm">{ax.noAccounts}</div>
          ) : viewMode === "member" ? (
            <>
              {persons.map((p: any, idx: number) => <MemberPanel key={p.id} person={p} idx={idx} />)}
              <SharedPanel />
            </>
          ) : (
            <ByTypeView />
          )}

        </div>
      </AppShell>
    </AccountCtx.Provider>
  );
}
