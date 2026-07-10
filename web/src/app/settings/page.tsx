"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { usePersons, usePriceLookupSetting, useSetPriceLookupSetting, useUpdatePerson } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { useTheme } from "@/lib/context/ThemeContext";
import { apiClient } from "@/lib/api/client";
import { Sun, Moon, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { LabelManager } from "@/components/settings/LabelManager";
import { TaxProfileSection } from "@/components/settings/TaxProfileSection";
import { LoansSection } from "@/components/settings/LoansSection";

export default function SettingsPage() {
  const { data: persons = [], refetch } = usePersons();
  const { data: priceLookup } = usePriceLookupSetting();
  const setPriceLookup = useSetPriceLookupSetting();
  const updatePerson = useUpdatePerson();
  const [newPersonName, setNewPersonName] = useState("");
  const [newPersonDob, setNewPersonDob] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [editingPersonId, setEditingPersonId] = useState<number | null>(null);
  const [editDob, setEditDob] = useState("");
  const { t, locale, setLocale } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const sx = t("settings");

  const handleAddPerson = async () => {
    if (!newPersonName.trim()) return;
    setSaving(true);
    try {
      await apiClient.post("/persons", {
        name: newPersonName,
        is_primary: persons.length === 0,
        date_of_birth: newPersonDob || null,
      });
      await refetch();
      setNewPersonName("");
      setNewPersonDob("");
      setMsg(sx.personAdded);
    } catch {
      setMsg(sx.error);
    } finally {
      setSaving(false);
    }
  };

  const startEditPerson = (p: any) => {
    setEditingPersonId(p.id);
    setEditDob(p.date_of_birth || "");
  };

  const handleSavePersonDob = async (id: number) => {
    await updatePerson.mutateAsync({ id, date_of_birth: editDob || null });
    setEditingPersonId(null);
  };

  const handleExport = async () => {
    const res = await apiClient.get("/export", { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ledgerly_export.zip";
    a.click();
  };

  const sectionClass = "bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5";

  return (
    <AppShell>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{sx.title}</h1>

        {/* Appearance & Language */}
        <section className={`${sectionClass} space-y-4`}>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.appearance}</h2>

          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-foreground">{sx.theme}</span>
            <div className="flex gap-2">
              <button
                onClick={() => theme === "dark" && toggleTheme()}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                  theme === "light"
                    ? "bg-brand border-brand text-white"
                    : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                )}
              >
                <Sun className="h-3.5 w-3.5" />
                {sx.lightMode}
              </button>
              <button
                onClick={() => theme === "light" && toggleTheme()}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                  theme === "dark"
                    ? "bg-brand border-brand text-white"
                    : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                )}
              >
                <Moon className="h-3.5 w-3.5" />
                {sx.darkMode}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between border-t dark:border-border pt-4">
            <span className="text-sm text-slate-700 dark:text-foreground">{sx.language}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setLocale("fr")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                  locale === "fr"
                    ? "bg-brand border-brand text-white"
                    : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                )}
              >
                <Globe className="h-3.5 w-3.5" />
                FR
              </button>
              <button
                onClick={() => setLocale("en")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                  locale === "en"
                    ? "bg-brand border-brand text-white"
                    : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                )}
              >
                <Globe className="h-3.5 w-3.5" />
                EN
              </button>
            </div>
          </div>
        </section>

        {/* Household members */}
        <section className={`${sectionClass} space-y-4`}>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.members}</h2>
          {persons.length > 0 ? (
            <ul className="space-y-2">
              {persons.map((p: any) => (
                <li key={p.id} className="py-2 border-b border-surface-border dark:border-border last:border-0">
                  <div className="flex items-center gap-3 group">
                    <div className="w-7 h-7 rounded-full bg-brand-50 text-brand-600 font-semibold text-xs flex items-center justify-center">
                      {p.name[0]}
                    </div>
                    <span className="text-sm text-slate-700 dark:text-foreground">{p.name}</span>
                    {p.is_primary && (
                      <span className="text-xs bg-brand-50 text-brand-600 dark:bg-indigo-950 dark:text-indigo-400 px-2 py-0.5 rounded-full">
                        {sx.primary}
                      </span>
                    )}
                    {p.date_of_birth && (
                      <span className="text-xs text-slate-400 dark:text-muted-foreground">{p.date_of_birth}</span>
                    )}
                    <button
                      onClick={() => startEditPerson(p)}
                      className="ml-auto text-xs text-brand opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
                    >
                      {sx.edit}
                    </button>
                  </div>
                  {editingPersonId === p.id && (
                    <div className="mt-2 ml-10 flex items-end gap-2">
                      <div>
                        <label className="text-xs text-slate-500 dark:text-muted-foreground" title={sx.dateOfBirthHint}>
                          {sx.dateOfBirth}
                        </label>
                        <input
                          type="date"
                          value={editDob}
                          onChange={e => setEditDob(e.target.value)}
                          className="block mt-1 text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground"
                        />
                      </div>
                      <button
                        onClick={() => handleSavePersonDob(p.id)}
                        className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700"
                      >
                        {sx.save}
                      </button>
                      <button
                        onClick={() => setEditingPersonId(null)}
                        className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
                      >
                        {sx.cancel}
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400 dark:text-muted-foreground">{sx.noMembers}</p>
          )}
          <div className="flex gap-2">
            <input
              value={newPersonName}
              onChange={e => setNewPersonName(e.target.value)}
              placeholder={sx.memberPlaceholder}
              className="flex-1 text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground"
            />
            <input
              type="date"
              value={newPersonDob}
              onChange={e => setNewPersonDob(e.target.value)}
              title={sx.dateOfBirthHint}
              className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground"
            />
            <button
              onClick={handleAddPerson}
              disabled={saving || !newPersonName.trim()}
              className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
            >
              {sx.addMember}
            </button>
          </div>
          {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
        </section>

        {/* Tax profile */}
        <section className={sectionClass}>
          <TaxProfileSection />
        </section>

        {/* Loans */}
        <section className={sectionClass}>
          <LoansSection />
        </section>

        {/* Labels & rules */}
        <section className={sectionClass}>
          <LabelManager />
        </section>

        {/* Price data (external, opt-in) */}
        <section className={`${sectionClass} space-y-3`}>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.priceDataTitle}</h2>
          <div className="flex items-center justify-between py-2">
            <div className="pr-4">
              <p className="text-sm text-slate-700 dark:text-foreground">{sx.priceDataLabel}</p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">{sx.priceDataDesc}</p>
            </div>
            <button
              role="switch"
              aria-checked={priceLookup?.price_lookup_enabled ?? false}
              onClick={() => setPriceLookup.mutate(!(priceLookup?.price_lookup_enabled ?? false))}
              className={cn(
                "relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors",
                priceLookup?.price_lookup_enabled ? "bg-brand" : "bg-slate-200 dark:bg-secondary"
              )}
            >
              <span
                className={cn(
                  "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                  priceLookup?.price_lookup_enabled ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
          </div>
        </section>

        {/* Data & privacy */}
        <section className={`${sectionClass} space-y-3`}>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.data}</h2>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm text-slate-700 dark:text-foreground">{sx.exportTitle}</p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.exportDesc}</p>
            </div>
            <button onClick={handleExport} className="text-sm text-brand font-medium hover:underline">
              {sx.exportBtn}
            </button>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-surface-border dark:border-border">
            <div>
              <p className="text-sm text-danger">{sx.deleteTitle}</p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.deleteDesc}</p>
            </div>
            <button
              onClick={async () => {
                if (confirm(sx.deleteConfirm)) {
                  await apiClient.delete("/account/data");
                }
              }}
              className="text-sm text-danger font-medium hover:underline"
            >
              {sx.deleteBtn}
            </button>
          </div>
        </section>

        {/* App info */}
        <section className={sectionClass}>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-3">{sx.about}</h2>
          <dl className="space-y-1 text-sm">
            {([
              [sx.application, "Ledgerly v0.1.0"],
              [sx.stack, "FastAPI · Next.js 14 · PostgreSQL 16"],
              [sx.data2, locale === "fr" ? "100% locales — aucune donnée ne quitte votre machine" : "100% local — no data leaves your machine"],
              [sx.licence, "MIT"],
            ] as [string, string][]).map(([k, v]) => (
              <div key={k} className="flex gap-4">
                <dt className="text-slate-400 dark:text-muted-foreground w-28 flex-shrink-0">{k}</dt>
                <dd className="text-slate-700 dark:text-foreground">{v}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </AppShell>
  );
}
