"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { useResidency, useSetResidency, useTreaties } from "@/lib/api/hooks";

interface Person {
  id: number;
  name: string;
  is_primary: boolean;
}

interface Treaty {
  country_code: string;
  country_name: string;
  default_elimination_method: string;
  treaty_reference: string;
}

function PersonResidencyRow({
  person,
  treaties,
  tf,
}: {
  person: Person;
  treaties: Treaty[];
  tf: Record<string, string>;
}) {
  const { data: residency } = useResidency(person.id);
  const setResidency = useSetResidency();
  const [expanded, setExpanded] = useState(false);
  const [homeCountryCode, setHomeCountryCode] = useState("");
  const [homeCountryTaxId, setHomeCountryTaxId] = useState("");
  const [frenchTaxNumber, setFrenchTaxNumber] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (residency) {
      setHomeCountryCode(residency.home_country_code ?? "");
      setHomeCountryTaxId(residency.home_country_tax_id ?? "");
      setFrenchTaxNumber(residency.french_tax_number ?? "");
    }
  }, [residency]);

  const matchedTreaty = treaties.find(
    (t) => t.country_code === homeCountryCode.toUpperCase()
  );

  const handleSave = async () => {
    setMsg("");
    try {
      await setResidency.mutateAsync({
        personId: person.id,
        body: {
          home_country_code: homeCountryCode ? homeCountryCode.toUpperCase() : null,
          home_country_tax_id: homeCountryTaxId || null,
          french_tax_number: frenchTaxNumber || null,
        },
      });
      setMsg(tf.saved);
    } catch {
      setMsg(tf.error);
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
          {residency?.home_country_code && (
            <span className="text-xs bg-brand-50 text-brand-600 dark:bg-indigo-950 dark:text-indigo-400 px-2 py-0.5 rounded-full">
              {residency.home_country_code}
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
          <div className="flex flex-wrap gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
              {tf.homeCountryCode}
              <input
                type="text"
                maxLength={2}
                value={homeCountryCode}
                onChange={(e) => setHomeCountryCode(e.target.value.toUpperCase())}
                placeholder="IN"
                className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20 w-24"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
              {tf.homeCountryTaxId}
              <input
                type="text"
                value={homeCountryTaxId}
                onChange={(e) => setHomeCountryTaxId(e.target.value)}
                className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
              {tf.frenchTaxNumber}
              <input
                type="text"
                value={frenchTaxNumber}
                onChange={(e) => setFrenchTaxNumber(e.target.value)}
                className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>
          </div>

          {homeCountryCode && (
            <p className="text-xs text-slate-500 dark:text-muted-foreground">
              {matchedTreaty
                ? `${tf.treatyMatched}: ${matchedTreaty.treaty_reference} (${
                    matchedTreaty.default_elimination_method === "credit_equal_to_french_tax"
                      ? tf.methodCredit
                      : tf.methodExemption
                  })`
                : tf.treatyUnseeded}
            </p>
          )}

          <button
            type="button"
            onClick={handleSave}
            disabled={setResidency.isPending}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
          >
            {tf.save}
          </button>
          {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}
        </div>
      )}
    </div>
  );
}

export function ResidencyStep({
  persons,
  tf,
}: {
  persons: Person[];
  tf: Record<string, string>;
}) {
  const { data: treaties = [] } = useTreaties();

  return (
    <div className="space-y-1">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tf.residencyTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1 mb-2">{tf.residencyDesc}</p>
      </div>
      {persons.length === 0 ? (
        <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.noMembers}</p>
      ) : (
        persons.map((p) => (
          <PersonResidencyRow key={p.id} person={p} treaties={treaties as Treaty[]} tf={tf} />
        ))
      )}
    </div>
  );
}
