"use client";

import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import {
  usePersons, useLoans, useCreateLoan, useUpdateLoan, useDeleteLoan,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatPct } from "@/lib/format/money";
import { InstitutionCombobox } from "@/components/InstitutionCombobox";

const LOAN_TYPES = ["mortgage", "car", "personal", "student", "other"] as const;

const BLANK_FORM = {
  name: "", type: "mortgage" as string, principal: "", annual_rate: "", term_months: "",
  start_date: "", payment_day: "5", currency: "EUR", institution: "",
  owner_id: "", joint_owner_id: "", ownership_pct: "100",
  manual_payment_enabled: false, manual_payment: "", notes: "",
};

// Cosmetic fields only — matches the backend's LoanUpdateIn scope exactly (no
// notes input here, since sending an always-empty `notes` on every edit would
// silently overwrite any existing note).
const EDIT_BLANK = { name: "", type: "mortgage" as string, payment_day: "5", institution: "" };

/** Same French annuité-constante formula as api/app/core/amortization.py, used here
 * only for a live client-side preview — the backend is the source of truth. */
function computeEmiPreview(principal: number, annualRatePct: number, termMonths: number): number | null {
  if (!principal || !annualRatePct || !termMonths) return null;
  const r = annualRatePct / 100 / 12;
  if (r === 0) return principal / termMonths;
  const emi = (principal * r) / (1 - Math.pow(1 + r, -termMonths));
  return Number.isFinite(emi) ? emi : null;
}

export function LoansSection() {
  const { t } = useLanguage();
  const sx = t("settings");
  const { data: persons = [] } = usePersons();
  const { data: loans = [] } = useLoans();
  const createLoan = useCreateLoan();
  const updateLoan = useUpdateLoan();
  const deleteLoan = useDeleteLoan();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(BLANK_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(EDIT_BLANK);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  const typeLabel = (v: string) => (sx as any)[`loansType_${v}`] ?? v;

  const principalNum = parseFloat(form.principal);
  const rateNum = parseFloat(form.annual_rate);
  const termNum = parseInt(form.term_months, 10);
  const computedEmi = computeEmiPreview(principalNum, rateNum, termNum);
  const firstInterest = principalNum && rateNum ? principalNum * (rateNum / 100 / 12) : 0;
  const manualPaymentNum = parseFloat(form.manual_payment);
  const manualPaymentTooLow =
    form.manual_payment_enabled && form.manual_payment !== "" &&
    !Number.isNaN(manualPaymentNum) && manualPaymentNum <= firstInterest;

  const canSubmit =
    form.name && form.owner_id && principalNum > 0 && rateNum >= 0 && termNum > 0 && form.start_date &&
    (!form.manual_payment_enabled ||
      (form.manual_payment !== "" && !Number.isNaN(manualPaymentNum) && !manualPaymentTooLow));

  const handleCreate = async () => {
    setMsg("");
    try {
      await createLoan.mutateAsync({
        name: form.name,
        type: form.type,
        principal: form.principal,
        annual_rate: (rateNum / 100).toString(),
        term_months: termNum,
        start_date: form.start_date,
        payment_day: parseInt(form.payment_day, 10) || 5,
        currency: form.currency,
        manual_payment: form.manual_payment_enabled ? form.manual_payment : null,
        institution: form.institution || null,
        owner_id: Number(form.owner_id),
        joint_owner_id: form.joint_owner_id ? Number(form.joint_owner_id) : null,
        ownership_pct: parseFloat(form.ownership_pct) || 100,
        notes: form.notes || null,
      });
      setForm(BLANK_FORM);
      setShowForm(false);
      setMsg(sx.loansSaved);
    } catch {
      setMsg(sx.error);
    }
  };

  const startEdit = (l: any) => {
    setEditForm({
      name: l.name, type: l.type,
      payment_day: String(l.payment_day), institution: l.institution || "",
    });
    setEditingId(l.id);
    setDeleteConfirmId(null);
  };

  const handleSaveEdit = async (id: number) => {
    setMsg("");
    try {
      await updateLoan.mutateAsync({
        id,
        name: editForm.name,
        type: editForm.type,
        payment_day: parseInt(editForm.payment_day, 10) || 5,
        institution: editForm.institution || null,
      });
      setEditingId(null);
      setMsg(sx.loansSaved);
    } catch {
      setMsg(sx.error);
    }
  };

  const handleDelete = async (id: number) => {
    await deleteLoan.mutateAsync(id);
    setDeleteConfirmId(null);
  };

  const inputClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const selectClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none bg-white dark:bg-secondary dark:text-foreground";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.loansTitle}</h2>
          <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{sx.loansDesc}</p>
        </div>
        <button
          type="button"
          onClick={() => { setForm(BLANK_FORM); setShowForm((v) => !v); }}
          className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700 flex-shrink-0"
        >
          {sx.loansAdd}
        </button>
      </div>

      {loans.length > 0 ? (
        <ul className="space-y-2">
          {loans.map((l: any) => (
            <li key={l.id} className="border-b border-surface-border dark:border-border last:border-0 pb-3 last:pb-0">
              <div className="flex items-center gap-3 group py-1">
                <span className="text-sm font-medium text-slate-700 dark:text-foreground">{l.name}</span>
                <span className="text-xs bg-slate-100 text-slate-600 dark:bg-secondary dark:text-muted-foreground px-2 py-0.5 rounded-full">
                  {typeLabel(l.type)}
                </span>
                <span className="text-xs text-slate-400 dark:text-muted-foreground money">
                  {formatMoney(l.principal)} · {formatPct(Number(l.annual_rate) * 100)}
                </span>
                <div className="ml-auto flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => startEdit(l)} title={sx.loansEdit} className="p-1.5 rounded-lg text-slate-400 hover:text-brand hover:bg-slate-100 dark:hover:bg-secondary transition-colors">
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button onClick={() => { setDeleteConfirmId(l.id); setEditingId(null); }} title={sx.loansDelete} className="p-1.5 rounded-lg text-slate-400 hover:text-danger hover:bg-danger/10 transition-colors">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {editingId === l.id && (
                <div className="mt-2 grid grid-cols-2 gap-3 max-w-xl">
                  <div className="col-span-2">
                    <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansName}</label>
                    <input value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} className={inputClass} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansType}</label>
                    <select value={editForm.type} onChange={e => setEditForm(f => ({ ...f, type: e.target.value }))} className={selectClass}>
                      {LOAN_TYPES.map(v => <option key={v} value={v}>{typeLabel(v)}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansPaymentDay}</label>
                    <input type="number" min={1} max={31} value={editForm.payment_day} onChange={e => setEditForm(f => ({ ...f, payment_day: e.target.value }))} className={inputClass} />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansInstitution}</label>
                    <InstitutionCombobox value={editForm.institution} onChange={val => setEditForm(f => ({ ...f, institution: val }))} inputClass={inputClass} />
                  </div>
                  <div className="col-span-2 flex gap-2 mt-1">
                    <button onClick={() => handleSaveEdit(l.id)} className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700">
                      {sx.save}
                    </button>
                    <button onClick={() => setEditingId(null)} className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
                      {sx.cancel}
                    </button>
                  </div>
                </div>
              )}

              {deleteConfirmId === l.id && editingId !== l.id && (
                <div className="mt-2 flex items-center gap-3 bg-danger/5 border border-danger/20 rounded-lg px-3 py-2">
                  <p className="text-xs text-slate-600 dark:text-muted-foreground flex-1">{sx.loansDeleteConfirm}</p>
                  <button onClick={() => handleDelete(l.id)} className="text-xs font-medium text-white bg-danger hover:bg-danger/90 px-3 py-1.5 rounded-lg">
                    {sx.loansDelete}
                  </button>
                  <button onClick={() => setDeleteConfirmId(null)} className="text-xs text-slate-500 dark:text-muted-foreground px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
                    {sx.cancel}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      ) : (
        !showForm && <p className="text-sm text-slate-400 dark:text-muted-foreground">{sx.loansNone}</p>
      )}

      {showForm && (
        <div className="bg-slate-50 dark:bg-secondary/30 rounded-xl border border-surface-border dark:border-border p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansName}</label>
              <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansType}</label>
              <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))} className={selectClass}>
                {LOAN_TYPES.map(v => <option key={v} value={v}>{typeLabel(v)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansInstitution}</label>
              <InstitutionCombobox value={form.institution} onChange={val => setForm(f => ({ ...f, institution: val }))} inputClass={inputClass} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansPrincipal}</label>
              <input type="number" value={form.principal} onChange={e => setForm(f => ({ ...f, principal: e.target.value }))} className={`${inputClass} money`} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansRate}</label>
              <input type="number" step="0.01" value={form.annual_rate} onChange={e => setForm(f => ({ ...f, annual_rate: e.target.value }))} className={`${inputClass} money`} placeholder="1.85" />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansTermMonths}</label>
              <input type="number" value={form.term_months} onChange={e => setForm(f => ({ ...f, term_months: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansStartDate}</label>
              <input type="date" value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansPaymentDay}</label>
              <input type="number" min={1} max={31} value={form.payment_day} onChange={e => setForm(f => ({ ...f, payment_day: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansOwner}</label>
              <select value={form.owner_id} onChange={e => setForm(f => ({ ...f, owner_id: e.target.value, joint_owner_id: e.target.value === f.joint_owner_id ? "" : f.joint_owner_id }))} className={selectClass}>
                <option value="">—</option>
                {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansJointOwner}</label>
              <select value={form.joint_owner_id} onChange={e => setForm(f => ({ ...f, joint_owner_id: e.target.value }))} className={selectClass}>
                <option value="">—</option>
                {persons.filter((p: any) => !form.owner_id || String(p.id) !== form.owner_id).map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansOwnershipPct}</label>
              <input type="number" min={1} max={100} value={form.ownership_pct} onChange={e => setForm(f => ({ ...f, ownership_pct: e.target.value }))} className={`${inputClass} money`} />
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-surface-border dark:border-border pt-3">
            <div className="pr-4">
              <p className="text-sm text-slate-700 dark:text-foreground">{sx.loansManualEmiToggle}</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={form.manual_payment_enabled}
              onClick={() => setForm(f => ({ ...f, manual_payment_enabled: !f.manual_payment_enabled }))}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${
                form.manual_payment_enabled ? "bg-brand" : "bg-slate-200 dark:bg-secondary"
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${form.manual_payment_enabled ? "translate-x-6" : "translate-x-1"}`} />
            </button>
          </div>

          {form.manual_payment_enabled ? (
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{sx.loansManualEmiInput}</label>
              <input type="number" value={form.manual_payment} onChange={e => setForm(f => ({ ...f, manual_payment: e.target.value }))} className={`${inputClass} money max-w-xs`} />
              {manualPaymentTooLow && <p className="text-xs text-danger mt-1">{sx.loansManualEmiTooLow}</p>}
            </div>
          ) : (
            computedEmi !== null && (
              <p className="text-xs text-slate-500 dark:text-muted-foreground">
                {sx.loansComputedEmi}: <span className="money font-medium text-slate-700 dark:text-foreground">{formatMoney(computedEmi.toFixed(2))}</span>
              </p>
            )
          )}

          <div className="flex gap-2">
            <button onClick={handleCreate} disabled={!canSubmit || createLoan.isPending} className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700">
              {sx.loansAdd}
            </button>
            <button onClick={() => setShowForm(false)} className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary">
              {sx.cancel}
            </button>
          </div>
        </div>
      )}

      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}
