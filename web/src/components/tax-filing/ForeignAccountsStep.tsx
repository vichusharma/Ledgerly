"use client";

import { useState } from "react";
import { Upload, Trash2 } from "lucide-react";
import {
  useAccounts,
  usePreviewForeignAccount,
  useConfirmForeignAccount,
  useCreateForeignAccount,
  useForeignAccounts,
  useUpdateForeignAccount,
  useDeleteForeignAccount,
} from "@/lib/api/hooks";

const inputCls = "text-sm border border-surface-border dark:border-border rounded-lg px-2 py-1.5 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20 w-full";
const selectCls = inputCls;
const labelCls = "flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground";

interface Person { id: number; name: string }
interface Tf { [key: string]: string }

function BankStatementUpload({ personId, year, tf }: { personId: number; year: number; tf: Tf }) {
  const preview = usePreviewForeignAccount();
  const confirm = useConfirmForeignAccount();
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
      bank_name: result.bank_name ?? "",
      country_code: result.country_code ?? "",
      account_identifier_masked: result.account_identifier_masked ?? "",
      opened_this_year: result.opened_this_year ? "true" : "false",
      closed_this_year: result.closed_this_year ? "true" : "false",
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
      bank_name: form.bank_name,
      country_code: form.country_code.toUpperCase(),
      account_identifier_masked: form.account_identifier_masked || null,
      opened_this_year: form.opened_this_year === "true",
      closed_this_year: form.closed_this_year === "true",
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
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.bankStatementTitle}</h4>
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
            <label className={labelCls}>{tf.bankName}
              <input value={form.bank_name} onChange={(e) => setForm((f) => ({ ...f, bank_name: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.country}
              <input maxLength={2} value={form.country_code} onChange={(e) => setForm((f) => ({ ...f, country_code: e.target.value.toUpperCase() }))} className={inputCls} placeholder="US" />
            </label>
            <label className={labelCls}>{tf.accountMasked}
              <input value={form.account_identifier_masked} onChange={(e) => setForm((f) => ({ ...f, account_identifier_masked: e.target.value }))} className={inputCls} />
            </label>
            <label className={labelCls}>{tf.status}
              <select
                value={form.opened_this_year === "true" ? "opened" : form.closed_this_year === "true" ? "closed" : "none"}
                onChange={(e) => setForm((f) => ({
                  ...f,
                  opened_this_year: e.target.value === "opened" ? "true" : "false",
                  closed_this_year: e.target.value === "closed" ? "true" : "false",
                }))}
                className={selectCls}
              >
                <option value="none">{tf.statusNone}</option>
                <option value="opened">{tf.statusOpened}</option>
                <option value="closed">{tf.statusClosed}</option>
              </select>
            </label>
          </div>
          <button
            onClick={handleConfirm}
            disabled={confirm.isPending || !form.bank_name || !form.country_code}
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

function ManualForeignAccountEntry({
  personId, year, accounts, tf,
}: { personId: number; year: number; accounts: any[]; tf: Tf }) {
  const create = useCreateForeignAccount();
  const [form, setForm] = useState({ bank_name: "", country_code: "", account_identifier_masked: "", account_id: "" });
  const [msg, setMsg] = useState("");

  const handleSubmit = async () => {
    setMsg("");
    try {
      await create.mutateAsync({
        person_id: personId, tax_year: year,
        bank_name: form.bank_name,
        country_code: form.country_code.toUpperCase(),
        account_identifier_masked: form.account_identifier_masked || null,
        account_id: form.account_id ? Number(form.account_id) : null,
      });
      setForm({ bank_name: "", country_code: "", account_identifier_masked: "", account_id: "" });
      setMsg(tf.saved);
    } catch {
      setMsg(tf.error);
    }
  };

  return (
    <div className="border border-dashed border-surface-border dark:border-border rounded-lg p-3 space-y-2">
      <h4 className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.manualEntryTitle}</h4>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <input value={form.bank_name} onChange={(e) => setForm((f) => ({ ...f, bank_name: e.target.value }))} className={inputCls} placeholder={tf.bankName} />
        <input maxLength={2} value={form.country_code} onChange={(e) => setForm((f) => ({ ...f, country_code: e.target.value.toUpperCase() }))} className={inputCls} placeholder={tf.country} />
        <input value={form.account_identifier_masked} onChange={(e) => setForm((f) => ({ ...f, account_identifier_masked: e.target.value }))} className={inputCls} placeholder={tf.accountMasked} />
        <select value={form.account_id} onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))} className={selectCls}>
          <option value="">{tf.linkExistingAccount}</option>
          {accounts.map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
      </div>
      <button
        onClick={handleSubmit}
        disabled={create.isPending || !form.bank_name || !form.country_code}
        className="text-xs font-medium text-brand hover:underline disabled:opacity-50"
      >
        {tf.addManualEntry}
      </button>
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
    </div>
  );
}

function AccountsTable({ personId, year, tf }: { personId: number; year: number; tf: Tf }) {
  const { data: declarations = [] } = useForeignAccounts(personId || undefined, year);
  const updateForeignAccount = useUpdateForeignAccount();
  const deleteForeignAccount = useDeleteForeignAccount();

  if (declarations.length === 0) {
    return <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.noDeclarations}</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-xs text-slate-400 dark:text-muted-foreground text-left">
          <th className="py-1.5 font-medium">{tf.bankName}</th>
          <th className="py-1.5 font-medium">{tf.country}</th>
          <th className="py-1.5 font-medium">{tf.accountMasked}</th>
          <th className="py-1.5 font-medium">{tf.status}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {declarations.map((d: any) => (
          <tr key={d.id} className="border-t border-surface-border dark:border-border">
            <td className="py-1.5">{d.bank_name}</td>
            <td className="py-1.5">{d.country_code}</td>
            <td className="py-1.5">{d.account_identifier_masked ?? "-"}</td>
            <td className="py-1.5">
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox" checked={d.closed_this_year}
                  onChange={(e) => updateForeignAccount.mutate({ id: d.id, body: { closed_this_year: e.target.checked } })}
                />
                {tf.statusClosed}
              </label>
            </td>
            <td className="py-1.5 text-right">
              <button onClick={() => deleteForeignAccount.mutate(d.id)} className="text-slate-400 hover:text-danger">
                <Trash2 size={14} />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ForeignAccountsStep({ persons, year, tf }: { persons: Person[]; year: number; tf: Tf }) {
  const [personId, setPersonId] = useState<number | "">(persons[0]?.id ?? "");
  const { data: accounts = [] } = useAccounts();

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tf.foreignAccountsTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{tf.foreignAccountsDesc}</p>
      </div>

      <label className={labelCls + " w-fit"}>{tf.person}
        <select value={personId} onChange={(e) => setPersonId(Number(e.target.value))} className={selectCls}>
          {persons.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </label>

      {personId && (
        <>
          <BankStatementUpload personId={personId as number} year={year} tf={tf} />
          <ManualForeignAccountEntry personId={personId as number} year={year} accounts={accounts} tf={tf} />

          <div>
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-2">{tf.existingDeclarations}</h3>
            <AccountsTable personId={personId as number} year={year} tf={tf} />
          </div>
        </>
      )}
    </div>
  );
}
