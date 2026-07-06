"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import {
  usePersons,
  useTaxProfile,
  useSetTaxProfile,
  useHouseholdTaxSettings,
  useSetHouseholdTaxSettings,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";

interface Person {
  id: number;
  name: string;
  is_primary: boolean;
}

function PersonImpatriateRow({ person, sx }: { person: Person; sx: Record<string, string> }) {
  const { data: profile } = useTaxProfile(person.id);
  const setProfile = useSetTaxProfile();
  const [expanded, setExpanded] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [arrivalDate, setArrivalDate] = useState("");
  const [method, setMethod] = useState("flat_30");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (profile) {
      setEnabled(profile.impatriate_enabled);
      setArrivalDate(profile.impatriate_arrival_date ?? "");
      setMethod(profile.impatriate_election_method ?? "flat_30");
    }
  }, [profile]);

  const handleSave = async () => {
    setMsg("");
    try {
      await setProfile.mutateAsync({
        personId: person.id,
        body: {
          impatriate_enabled: enabled,
          impatriate_arrival_date: enabled ? arrivalDate || null : null,
          impatriate_election_method: enabled ? method : null,
        },
      });
      setMsg(sx.taxProfileSaved);
    } catch {
      setMsg(sx.error);
    }
  };

  return (
    <div className="border-b border-surface-border dark:border-border last:border-0">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center justify-between py-3 text-sm hover:bg-slate-50 dark:hover:bg-secondary"
      >
        <span className="flex items-center gap-2 font-medium text-slate-700 dark:text-foreground">
          {person.name}
          {profile?.impatriate_enabled && (
            <span className="text-xs bg-brand-50 text-brand-600 dark:bg-indigo-950 dark:text-indigo-400 px-2 py-0.5 rounded-full">
              {sx.impatriateActive}
            </span>
          )}
        </span>
        <ChevronDown
          size={16}
          className={`text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="pb-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="pr-4">
              <p className="text-sm text-slate-700 dark:text-foreground">{sx.impatriateToggle}</p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">{sx.impatriateDesc}</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={enabled}
              onClick={() => setEnabled((v) => !v)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${
                enabled ? "bg-brand" : "bg-slate-200 dark:bg-secondary"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          {enabled && (
            <div className="flex flex-wrap gap-3">
              <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
                {sx.arrivalDate}
                <input
                  type="date"
                  value={arrivalDate}
                  onChange={(e) => setArrivalDate(e.target.value)}
                  className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
                {sx.electionMethod}
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20"
                >
                  <option value="flat_30">{sx.electionFlat30}</option>
                  <option value="specific_premium">{sx.electionSpecificPremium}</option>
                </select>
              </label>
            </div>
          )}
          {enabled && method === "specific_premium" && (
            <p className="text-xs text-amber-600 dark:text-amber-400">{sx.specificPremiumNotComputed}</p>
          )}

          <button
            type="button"
            onClick={handleSave}
            disabled={setProfile.isPending}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
          >
            {sx.save}
          </button>
          {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
        </div>
      )}
    </div>
  );
}

export function TaxProfileSection() {
  const { t } = useLanguage();
  const sx = t("settings");
  const { data: persons = [] } = usePersons();
  const { data: householdSettings } = useHouseholdTaxSettings();
  const setHouseholdSettings = useSetHouseholdTaxSettings();

  const [filingStatus, setFilingStatus] = useState("single");
  const [dependentIds, setDependentIds] = useState<number[]>([]);
  const [householdMsg, setHouseholdMsg] = useState("");

  useEffect(() => {
    if (householdSettings) {
      setFilingStatus(householdSettings.filing_status);
      setDependentIds(householdSettings.dependent_person_ids ?? []);
    }
  }, [householdSettings]);

  const toggleDependent = (id: number) =>
    setDependentIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));

  const handleSaveHousehold = async () => {
    setHouseholdMsg("");
    try {
      await setHouseholdSettings.mutateAsync({
        filing_status: filingStatus,
        dependent_person_ids: dependentIds,
      });
      setHouseholdMsg(sx.taxProfileSaved);
    } catch {
      setHouseholdMsg(sx.error);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.taxProfileTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{sx.taxProfileDesc}</p>
      </div>

      {/* Household filing status & dependents */}
      <div className="space-y-3 pb-4 border-b border-surface-border dark:border-border">
        <p className="text-sm text-slate-700 dark:text-foreground">{sx.filingStatus}</p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setFilingStatus("single")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              filingStatus === "single"
                ? "bg-brand border-brand text-white"
                : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
            }`}
          >
            {sx.filingStatusSingle}
          </button>
          <button
            type="button"
            onClick={() => setFilingStatus("married_pacs")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              filingStatus === "married_pacs"
                ? "bg-brand border-brand text-white"
                : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
            }`}
          >
            {sx.filingStatusMarriedPacs}
          </button>
        </div>

        <p className="text-sm text-slate-700 dark:text-foreground pt-2">{sx.dependents}</p>
        {persons.length === 0 ? (
          <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.noMembers}</p>
        ) : (
          <div className="flex flex-wrap gap-3">
            {(persons as Person[]).map((p) => (
              <label
                key={p.id}
                className="flex items-center gap-2 text-sm text-slate-700 dark:text-foreground"
              >
                <input
                  type="checkbox"
                  checked={dependentIds.includes(p.id)}
                  onChange={() => toggleDependent(p.id)}
                  className="rounded border-surface-border dark:border-border"
                />
                {p.name}
              </label>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={handleSaveHousehold}
          disabled={setHouseholdSettings.isPending}
          className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
        >
          {sx.save}
        </button>
        {householdMsg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{householdMsg}</p>}
      </div>

      {/* Per-person impatriate regime */}
      <div>
        <p className="text-sm text-slate-700 dark:text-foreground mb-2">{sx.impatriateSection}</p>
        {persons.length === 0 ? (
          <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.noMembers}</p>
        ) : (
          (persons as Person[]).map((p) => <PersonImpatriateRow key={p.id} person={p} sx={sx} />)
        )}
      </div>
    </div>
  );
}
