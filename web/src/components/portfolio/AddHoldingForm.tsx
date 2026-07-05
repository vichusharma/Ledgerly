"use client";

import { useEffect, useRef, useState } from "react";
import {
  useAccounts, usePersons, useAddHolding, useInstrumentLookup, usePriceLookupSetting,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";

const BLANK_FORM = {
  isin: "", quantity: "", account_id: "", settled_at: new Date().toISOString().slice(0, 10),
  price: "", name: "", ticker: "", currency: "EUR",
};

const inputClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
const selectClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none bg-white dark:bg-secondary dark:text-foreground";

export function AddHoldingForm() {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(BLANK_FORM);
  const [lookupStatus, setLookupStatus] = useState<"idle" | "pending" | "found" | "not_found">("idle");

  const { data: accounts = [] } = useAccounts();
  const { data: persons = [] } = usePersons();
  const { data: priceLookup } = usePriceLookupSetting();
  const lookupEnabled = priceLookup?.price_lookup_enabled ?? false;
  const lookup = useInstrumentLookup();
  const addHolding = useAddHolding();

  const { t } = useLanguage();
  const px = t("portfolio");

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const isin = form.isin.trim().toUpperCase();
    if (!lookupEnabled || isin.length < 10) {
      setLookupStatus("idle");
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLookupStatus("pending");
      try {
        const result = await lookup.mutateAsync(isin);
        setForm(f => ({
          ...f,
          name: result.name, ticker: result.ticker ?? "", currency: result.currency,
          price: String(result.price),
        }));
        setLookupStatus("found");
      } catch {
        setLookupStatus("not_found");
      }
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.isin, lookupEnabled]);

  const accountLabel = (a: any) => {
    const owner = persons.find((p: any) => p.id === a.owner_id);
    const joint = a.joint_owner_id ? persons.find((p: any) => p.id === a.joint_owner_id) : null;
    return `${a.name} — ${owner?.name ?? ""}${joint ? ` & ${joint.name}` : ""}`;
  };

  const canSubmit =
    lookupEnabled && lookupStatus === "found" && !!form.quantity && !!form.account_id && !!form.price;

  const handleSubmit = async () => {
    await addHolding.mutateAsync({
      isin: form.isin.trim().toUpperCase(),
      quantity: Number(form.quantity),
      account_id: Number(form.account_id),
      price: Number(form.price),
      settled_at: form.settled_at,
      name: form.name || undefined,
      ticker: form.ticker || undefined,
      currency: form.currency || undefined,
    });
    setForm(BLANK_FORM);
    setLookupStatus("idle");
    setShowForm(false);
  };

  return (
    <div className="col-span-12">
      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700"
        >
          {px.addHolding}
        </button>
      ) : (
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{px.addHolding}</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{px.isin}</label>
              <input
                value={form.isin}
                onChange={e => setForm(f => ({ ...f, isin: e.target.value }))}
                className={inputClass}
                placeholder={px.isinPlaceholder}
              />
              {lookupEnabled && lookupStatus === "pending" && (
                <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{px.lookupPending}</p>
              )}
              {lookupEnabled && lookupStatus === "not_found" && (
                <p className="text-xs text-warning mt-1">{px.lookupFailed}</p>
              )}
              {lookupEnabled && lookupStatus === "found" && (
                <p className="text-xs text-success mt-1">{form.name} ({form.ticker}) — {form.currency}</p>
              )}
              {!lookupEnabled && (
                <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{px.lookupDisabledHint}</p>
              )}
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{px.quantity}</label>
              <input
                type="number" min={0} step="any"
                value={form.quantity}
                onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))}
                className={`${inputClass} money`}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{px.account}</label>
              <select
                value={form.account_id}
                onChange={e => setForm(f => ({ ...f, account_id: e.target.value }))}
                className={selectClass}
              >
                <option value="">{t("accounts").select}</option>
                {accounts.map((a: any) => (
                  <option key={a.id} value={a.id}>{accountLabel(a)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{px.settledAt}</label>
              <input
                type="date"
                value={form.settled_at}
                onChange={e => setForm(f => ({ ...f, settled_at: e.target.value }))}
                className={inputClass}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{px.price}</label>
              <input
                type="number" min={0} step="any"
                value={form.price}
                onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
                className={`${inputClass} money`}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={!canSubmit || addHolding.isPending}
              className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
            >
              {px.submitHolding}
            </button>
            <button
              onClick={() => { setShowForm(false); setForm(BLANK_FORM); setLookupStatus("idle"); }}
              className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
            >
              {t("accounts").cancel}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
