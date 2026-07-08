"use client";

import { useState } from "react";
import { Upload, Trash2 } from "lucide-react";
import {
  useAccounts,
  useInstruments,
  usePreviewRsuVesting,
  useConfirmRsuVesting,
  usePreviewEsppPurchase,
  useConfirmEsppPurchase,
  usePreviewForeignIncome,
  useConfirmForeignIncome,
  useCreateForeignIncome,
  useForeignIncome,
  useUpdateForeignIncome,
  useDeleteForeignIncome,
} from "@/lib/api/hooks";

const inputCls = "text-sm border border-surface-border dark:border-border rounded-lg px-2 py-1.5 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20 w-full";
const selectCls = inputCls;
const labelCls = "flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground";

interface Person { id: number; name: string }
interface Tf { [key: string]: string }

// -- RSU vesting upload -------------------------------------------------

function RsuVestingUpload({
  accounts, instruments, personId, year, tf,
}: { accounts: any[]; instruments: any[]; personId: number; year: number; tf: Tf }) {
  const preview = usePreviewRsuVesting();
  const confirm = useConfirmRsuVesting();
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const handleFile = async (f: File) => {
    setFile(f);
    setMsg("");
    const fd = new FormData();
    fd.append("file", f);
    const result = await preview.mutateAsync(fd);
    setForm({
      account_id: "", instrument_id: "",
      grant_date: result.grant_date ?? "",
      total_shares: result.total_shares ?? "",
      cliff_months: String(result.cliff_months ?? 12),
      vesting_months: String(result.vesting_months ?? 48),
      grant_price: result.grant_price ?? "",
      vest_date: result.vest_date ?? "",
      vested_shares: result.vested_shares ?? "",
      vest_fmv: result.vest_fmv ?? "",
    });
  };

  const handleConfirm = async () => {
    if (!file) return;
    setMsg("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("payload", JSON.stringify({
      person_id: personId,
      account_id: Number(form.account_id),
      instrument_id: Number(form.instrument_id),
      tax_year: year,
      grant_date: form.grant_date,
      total_shares: form.total_shares,
      cliff_months: Number(form.cliff_months),
      vesting_months: Number(form.vesting_months),
      grant_price: form.grant_price,
      vest_date: form.vest_date,
      vested_shares: form.vested_shares,
      vest_fmv: form.vest_fmv,
    }));
    try {
      await confirm.mutateAsync(fd);
      setMsg(tf.saved);
      setFile(null);
      setForm({});
    } catch {
      setMsg(tf.error);
    }
  };

  return (
    <div className="border border-surface-border dark:border-border rounded-lg p-3 space-y-2">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.rsuVestingTitle}</h4>
      {!Object.keys(form).length ? (
        <label className="flex items-center gap-2 text-xs text-brand cursor-pointer w-fit">
          <Upload size={14} />
          {tf.uploadFile}
          <input
            type="file" accept="application/pdf" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
      ) : (
        <div className="space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <label className={labelCls}>{tf.account}
              <select value={form.account_id} onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))} className={selectCls}>
                <option value="">{tf.select}</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </label>
            <label className={labelCls}>{tf.instrument}
              <select value={form.instrument_id} onChange={(e) => setForm((f) => ({ ...f, instrument_id: e.target.value }))} className={selectCls}>
                <option value="">{tf.select}</option>
                {instruments.map((i: any) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </label>
            <label className={labelCls}>{tf.grantDate}
              <input type="date" value={form.grant_date} onChange={(e) => setForm((f) => ({ ...f, grant_date: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.vestDate}
              <input type="date" value={form.vest_date} onChange={(e) => setForm((f) => ({ ...f, vest_date: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.totalShares}
              <input value={form.total_shares} onChange={(e) => setForm((f) => ({ ...f, total_shares: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.vestedShares}
              <input value={form.vested_shares} onChange={(e) => setForm((f) => ({ ...f, vested_shares: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.grantPrice}
              <input value={form.grant_price} onChange={(e) => setForm((f) => ({ ...f, grant_price: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.vestFmv}
              <input value={form.vest_fmv} onChange={(e) => setForm((f) => ({ ...f, vest_fmv: e.target.value }))} className={`${inputCls} money`} />
            </label>
          </div>
          <button
            onClick={handleConfirm}
            disabled={confirm.isPending || !form.account_id || !form.instrument_id}
            className="bg-brand text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50 hover:bg-brand-700"
          >
            {tf.save}
          </button>
        </div>
      )}
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}

// -- ESPP purchase upload -------------------------------------------------

function EsppPurchaseUpload({
  accounts, instruments, personId, year, tf,
}: { accounts: any[]; instruments: any[]; personId: number; year: number; tf: Tf }) {
  const preview = usePreviewEsppPurchase();
  const confirm = useConfirmEsppPurchase();
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const handleFile = async (f: File) => {
    setFile(f);
    setMsg("");
    const fd = new FormData();
    fd.append("file", f);
    const result = await preview.mutateAsync(fd);
    setForm({
      account_id: "", instrument_id: "",
      purchase_date: result.purchase_date ?? "",
      shares: result.shares ?? "",
      purchase_price: result.purchase_price ?? "",
      fmv_at_purchase: result.fmv_at_purchase ?? "",
      discount_pct: result.discount_pct ?? "",
    });
  };

  const handleConfirm = async () => {
    if (!file) return;
    setMsg("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("payload", JSON.stringify({
      person_id: personId,
      account_id: Number(form.account_id),
      instrument_id: Number(form.instrument_id),
      tax_year: year,
      purchase_date: form.purchase_date,
      shares: form.shares,
      purchase_price: form.purchase_price,
      fmv_at_purchase: form.fmv_at_purchase,
      discount_pct: form.discount_pct || null,
    }));
    try {
      await confirm.mutateAsync(fd);
      setMsg(tf.saved);
      setFile(null);
      setForm({});
    } catch {
      setMsg(tf.error);
    }
  };

  return (
    <div className="border border-surface-border dark:border-border rounded-lg p-3 space-y-2">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.esppPurchaseTitle}</h4>
      {!Object.keys(form).length ? (
        <label className="flex items-center gap-2 text-xs text-brand cursor-pointer w-fit">
          <Upload size={14} />
          {tf.uploadFile}
          <input
            type="file" accept="application/pdf" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
      ) : (
        <div className="space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <label className={labelCls}>{tf.account}
              <select value={form.account_id} onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))} className={selectCls}>
                <option value="">{tf.select}</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </label>
            <label className={labelCls}>{tf.instrument}
              <select value={form.instrument_id} onChange={(e) => setForm((f) => ({ ...f, instrument_id: e.target.value }))} className={selectCls}>
                <option value="">{tf.select}</option>
                {instruments.map((i: any) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </label>
            <label className={labelCls}>{tf.purchaseDate}
              <input type="date" value={form.purchase_date} onChange={(e) => setForm((f) => ({ ...f, purchase_date: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.shares}
              <input value={form.shares} onChange={(e) => setForm((f) => ({ ...f, shares: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.purchasePrice}
              <input value={form.purchase_price} onChange={(e) => setForm((f) => ({ ...f, purchase_price: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.fmvAtPurchase}
              <input value={form.fmv_at_purchase} onChange={(e) => setForm((f) => ({ ...f, fmv_at_purchase: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.discountPct}
              <input value={form.discount_pct} onChange={(e) => setForm((f) => ({ ...f, discount_pct: e.target.value }))} className={`${inputCls} money`} />
            </label>
          </div>
          <button
            onClick={handleConfirm}
            disabled={confirm.isPending || !form.account_id || !form.instrument_id}
            className="bg-brand text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50 hover:bg-brand-700"
          >
            {tf.save}
          </button>
        </div>
      )}
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}

// -- Foreign dividend/interest upload -------------------------------------

function ForeignDividendUpload({ personId, year, tf }: { personId: number; year: number; tf: Tf }) {
  const preview = usePreviewForeignIncome();
  const confirm = useConfirmForeignIncome();
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const handleFile = async (f: File) => {
    setFile(f);
    setMsg("");
    const fd = new FormData();
    fd.append("file", f);
    const result = await preview.mutateAsync(fd);
    setForm({
      income_type: "foreign_dividend",
      source_country_code: result.source_country_code ?? "",
      source_description: result.source_description ?? "",
      gross_amount_eur: result.gross_amount_eur ?? "",
      foreign_tax_paid_eur: result.foreign_tax_paid_eur ?? "0",
    });
  };

  const handleConfirm = async () => {
    if (!file) return;
    setMsg("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("payload", JSON.stringify({
      person_id: personId,
      tax_year: year,
      income_type: form.income_type,
      source_country_code: form.source_country_code.toUpperCase(),
      source_description: form.source_description,
      gross_amount_eur: form.gross_amount_eur,
      foreign_tax_paid_eur: form.foreign_tax_paid_eur || "0",
    }));
    try {
      await confirm.mutateAsync(fd);
      setMsg(tf.saved);
      setFile(null);
      setForm({});
    } catch {
      setMsg(tf.error);
    }
  };

  return (
    <div className="border border-surface-border dark:border-border rounded-lg p-3 space-y-2">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.foreignDividendTitle}</h4>
      {!Object.keys(form).length ? (
        <label className="flex items-center gap-2 text-xs text-brand cursor-pointer w-fit">
          <Upload size={14} />
          {tf.uploadFile}
          <input
            type="file" accept="application/pdf" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </label>
      ) : (
        <div className="space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <label className={labelCls}>{tf.incomeType}
              <select value={form.income_type} onChange={(e) => setForm((f) => ({ ...f, income_type: e.target.value }))} className={selectCls}>
                <option value="foreign_dividend">{tf.incomeTypeDividend}</option>
                <option value="foreign_interest">{tf.incomeTypeInterest}</option>
                <option value="foreign_salary">{tf.incomeTypeSalary}</option>
                <option value="foreign_capital_gain">{tf.incomeTypeCapitalGain}</option>
                <option value="other">{tf.incomeTypeOther}</option>
              </select>
            </label>
            <label className={labelCls}>{tf.country}
              <input maxLength={2} value={form.source_country_code} onChange={(e) => setForm((f) => ({ ...f, source_country_code: e.target.value.toUpperCase() }))} className={inputCls} placeholder="US" />
            </label>
            <label className={labelCls}>{tf.description}
              <input value={form.source_description} onChange={(e) => setForm((f) => ({ ...f, source_description: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.grossAmount}
              <input value={form.gross_amount_eur} onChange={(e) => setForm((f) => ({ ...f, gross_amount_eur: e.target.value }))} className={`${inputCls} money`} />
            </label>
            <label className={labelCls}>{tf.foreignTaxPaid}
              <input value={form.foreign_tax_paid_eur} onChange={(e) => setForm((f) => ({ ...f, foreign_tax_paid_eur: e.target.value }))} className={`${inputCls} money`} />
            </label>
          </div>
          <button
            onClick={handleConfirm}
            disabled={confirm.isPending || !form.source_country_code || !form.gross_amount_eur}
            className="bg-brand text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50 hover:bg-brand-700"
          >
            {tf.save}
          </button>
        </div>
      )}
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}

// -- Manual entry (no source document, Feature J2-S7) ---------------------

function ManualForeignIncomeEntry({ personId, year, tf }: { personId: number; year: number; tf: Tf }) {
  const create = useCreateForeignIncome();
  const [form, setForm] = useState({
    income_type: "foreign_dividend", source_country_code: "", source_description: "",
    gross_amount_eur: "", foreign_tax_paid_eur: "0",
  });
  const [msg, setMsg] = useState("");

  const handleSubmit = async () => {
    setMsg("");
    try {
      await create.mutateAsync({
        person_id: personId, tax_year: year,
        income_type: form.income_type,
        source_country_code: form.source_country_code.toUpperCase(),
        source_description: form.source_description,
        gross_amount_eur: form.gross_amount_eur,
        foreign_tax_paid_eur: form.foreign_tax_paid_eur || "0",
      });
      setForm({ income_type: "foreign_dividend", source_country_code: "", source_description: "", gross_amount_eur: "", foreign_tax_paid_eur: "0" });
      setMsg(tf.saved);
    } catch {
      setMsg(tf.error);
    }
  };

  return (
    <div className="border border-dashed border-surface-border dark:border-border rounded-lg p-3 space-y-2">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.manualEntryTitle}</h4>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <select value={form.income_type} onChange={(e) => setForm((f) => ({ ...f, income_type: e.target.value }))} className={selectCls}>
          <option value="foreign_dividend">{tf.incomeTypeDividend}</option>
          <option value="foreign_interest">{tf.incomeTypeInterest}</option>
          <option value="foreign_salary">{tf.incomeTypeSalary}</option>
          <option value="foreign_capital_gain">{tf.incomeTypeCapitalGain}</option>
          <option value="other">{tf.incomeTypeOther}</option>
        </select>
        <input maxLength={2} value={form.source_country_code} onChange={(e) => setForm((f) => ({ ...f, source_country_code: e.target.value.toUpperCase() }))} className={inputCls} placeholder={tf.country} />
        <input value={form.source_description} onChange={(e) => setForm((f) => ({ ...f, source_description: e.target.value }))} className={inputCls} placeholder={tf.description} />
        <input value={form.gross_amount_eur} onChange={(e) => setForm((f) => ({ ...f, gross_amount_eur: e.target.value }))} className={`${inputCls} money`} placeholder={tf.grossAmount} />
        <input value={form.foreign_tax_paid_eur} onChange={(e) => setForm((f) => ({ ...f, foreign_tax_paid_eur: e.target.value }))} className={`${inputCls} money`} placeholder={tf.foreignTaxPaid} />
      </div>
      <button
        onClick={handleSubmit}
        disabled={create.isPending || !form.source_country_code || !form.gross_amount_eur}
        className="text-xs font-medium text-brand hover:underline disabled:opacity-50"
      >
        {tf.addManualEntry}
      </button>
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}

// -- Existing declarations table (with inline method override) -----------

function DeclarationsTable({ personId, year, tf }: { personId: number; year: number; tf: Tf }) {
  const { data: declarations = [] } = useForeignIncome(personId || undefined, year);
  const updateForeignIncome = useUpdateForeignIncome();
  const deleteForeignIncome = useDeleteForeignIncome();

  if (declarations.length === 0) {
    return <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.noDeclarations}</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-xs text-slate-400 dark:text-muted-foreground text-left">
          <th className="py-1.5 font-medium">{tf.country}</th>
          <th className="py-1.5 font-medium">{tf.description}</th>
          <th className="py-1.5 font-medium text-right">{tf.grossAmount}</th>
          <th className="py-1.5 font-medium">{tf.methodOverride}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {declarations.map((d: any) => (
          <tr key={d.id} className="border-t border-surface-border dark:border-border">
            <td className="py-1.5">{d.source_country_code}</td>
            <td className="py-1.5">{d.source_description}</td>
            <td className="py-1.5 text-right money">{d.gross_amount_eur}</td>
            <td className="py-1.5">
              <select
                value={d.elimination_method_override ?? ""}
                onChange={(e) => updateForeignIncome.mutate({
                  id: d.id,
                  body: { elimination_method_override: e.target.value || null },
                })}
                className="text-xs border border-surface-border dark:border-border rounded-lg px-2 py-1 bg-white dark:bg-secondary dark:text-foreground"
              >
                <option value="">{tf.methodAuto}</option>
                <option value="credit_equal_to_french_tax">{tf.methodCredit}</option>
                <option value="exemption_with_effective_rate">{tf.methodExemption}</option>
              </select>
            </td>
            <td className="py-1.5 text-right">
              <button onClick={() => deleteForeignIncome.mutate(d.id)} className="text-slate-400 hover:text-danger">
                <Trash2 size={14} />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// -- Step assembly ---------------------------------------------------------

export function ForeignIncomeStep({ persons, year, tf }: { persons: Person[]; year: number; tf: Tf }) {
  const [personId, setPersonId] = useState<number | "">(persons[0]?.id ?? "");
  const { data: accounts = [] } = useAccounts();
  const { data: instruments = [] } = useInstruments();

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tf.foreignIncomeTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{tf.foreignIncomeDesc}</p>
      </div>

      <label className={labelCls + " w-fit"}>{tf.person}
        <select value={personId} onChange={(e) => setPersonId(Number(e.target.value))} className={selectCls}>
          {persons.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </label>

      {personId && (
        <>
          <RsuVestingUpload accounts={accounts} instruments={instruments} personId={personId as number} year={year} tf={tf} />
          <EsppPurchaseUpload accounts={accounts} instruments={instruments} personId={personId as number} year={year} tf={tf} />
          <ForeignDividendUpload personId={personId as number} year={year} tf={tf} />
          <ManualForeignIncomeEntry personId={personId as number} year={year} tf={tf} />

          <div>
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-2">{tf.existingDeclarations}</h3>
            <DeclarationsTable personId={personId as number} year={year} tf={tf} />
          </div>
        </>
      )}
    </div>
  );
}
