"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiClient } from "@/lib/api/client";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatPct } from "@/lib/format/money";

interface SensitivityRow {
  retirement_age: number;
  retirement_year: number;
  quarters_validated: number;
  rate_applied: number;
  decote_quarters: number;
  surcote_quarters: number;
  monthly_base: number;
  monthly_complementary: number;
  monthly_total: number;
  replacement_ratio: number;
  achieves_full_rate: boolean;
}

interface PensionResult {
  sam: number;
  quarters_validated: number;
  quarters_required: number;
  total_agirc_arrco_points: number;
  planned: SensitivityRow;
  sensitivity: SensitivityRow[];
}

interface FormState {
  birth_year: string;
  career_start_year: string;
  current_annual_salary: string;
  salary_growth_rate: string;
  planned_retirement_year: string;
  bonus_quarters: string;
}

function RowBadge({ row }: { row: SensitivityRow }) {
  if (row.surcote_quarters > 0)
    return <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-medium">+{row.surcote_quarters}q</span>;
  if (!row.achieves_full_rate && row.decote_quarters > 0)
    return <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 font-medium">−{row.decote_quarters}q</span>;
  return <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium">✓</span>;
}

export default function PensionPage() {
  const { t } = useLanguage();
  const px = t("pension");

  const [form, setForm] = useState<FormState>({
    birth_year: "1985",
    career_start_year: "2007",
    current_annual_salary: "45000",
    salary_growth_rate: "0.02",
    planned_retirement_year: "2050",
    bonus_quarters: "0",
  });
  const [result, setResult] = useState<PensionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const calculate = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await apiClient.post<PensionResult>("/pension/project", {
        birth_year: parseInt(form.birth_year),
        career_start_year: parseInt(form.career_start_year),
        current_annual_salary: parseFloat(form.current_annual_salary),
        salary_growth_rate: parseFloat(form.salary_growth_rate),
        planned_retirement_year: parseInt(form.planned_retirement_year),
        bonus_quarters: parseInt(form.bonus_quarters) || 0,
      });
      setResult(data);
    } catch {
      setError(px.error);
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const labelClass = "text-xs font-medium text-slate-500 dark:text-muted-foreground";

  const interp = (tpl: string, vars: Record<string, string | number>) =>
    tpl.replace(/\{\{(\w+)\}\}/g, (_, k) => String(vars[k] ?? ""));

  // Build interpretation text
  const interpretation = (() => {
    if (!result) return null;
    const { planned, quarters_required } = result;
    const missing = quarters_required - planned.quarters_validated;
    if (planned.surcote_quarters > 0) {
      const n = planned.surcote_quarters;
      return interp(px.interpSurcote, { n, s: n > 1 ? "s" : "", pct: formatPct(n * 1.25, 2) });
    }
    if (!planned.achieves_full_rate && missing > 0) {
      const fullRateRow = result.sensitivity.find(r => r.achieves_full_rate && r.decote_quarters === 0);
      const fullRateInfo = fullRateRow
        ? " " + interp(px.interpFullRateAt, { year: fullRateRow.retirement_year, age: fullRateRow.retirement_age })
        : "";
      return interp(px.interpDecote, { n: missing, s: missing > 1 ? "s" : "", pct: formatPct(planned.decote_quarters * 1.25, 2) }) + fullRateInfo;
    }
    return interp(px.interpAchieved, { n: quarters_required });
  })();

  return (
    <AppShell>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{px.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{px.subtitle}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6 items-start">
          {/* ── Left: inputs ── */}
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5 space-y-4">
            <div>
              <label className={labelClass}>{px.birthYear}</label>
              <input type="number" value={form.birth_year} onChange={set("birth_year")}
                min={1940} max={2005} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>{px.careerStart}</label>
              <input type="number" value={form.career_start_year} onChange={set("career_start_year")}
                min={1960} max={2030} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>{px.currentSalary}</label>
              <input type="number" step="1000" value={form.current_annual_salary}
                onChange={set("current_annual_salary")} min={0} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>{px.salaryGrowth}</label>
              <div className="flex items-center gap-3 mt-1">
                <input
                  type="range" min={0} max={0.05} step={0.005}
                  value={form.salary_growth_rate}
                  onChange={set("salary_growth_rate")}
                  className="flex-1 accent-brand"
                />
                <span className="text-sm font-mono w-12 text-slate-700 dark:text-foreground">
                  {formatPct(parseFloat(form.salary_growth_rate) * 100, 1)}
                </span>
              </div>
            </div>
            <div>
              <label className={labelClass}>{px.retirementYear}</label>
              <input type="number" value={form.planned_retirement_year}
                onChange={set("planned_retirement_year")} min={2025} max={2080} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>{px.bonusQuarters}</label>
              <input type="number" value={form.bonus_quarters} onChange={set("bonus_quarters")}
                min={0} max={32} className={inputClass} />
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{px.bonusQuartersHint}</p>
            </div>

            {error && <p className="text-xs text-danger">{error}</p>}

            <button
              onClick={calculate}
              disabled={loading}
              className="w-full bg-brand text-white font-medium py-2.5 rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors text-sm"
            >
              {loading ? px.calculating : px.calculate}
            </button>
          </div>

          {/* ── Right: results ── */}
          {result ? (
            <div className="space-y-4">
              {/* KPI cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4">
                  <div className="flex items-center gap-1.5">
                    <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.samLabel}</p>
                    <span className="text-xs text-slate-400 dark:text-muted-foreground" title={px.samHint}>ⓘ</span>
                  </div>
                  <p className="text-lg font-semibold mt-1 money text-slate-900 dark:text-foreground">
                    {formatMoney(result.sam)}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">/an</p>
                </div>

                <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4">
                  <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.quartersLabel}</p>
                  <p className="text-lg font-semibold mt-1 text-slate-900 dark:text-foreground">
                    {result.quarters_validated}
                    <span className="text-sm font-normal text-slate-400 dark:text-muted-foreground"> / {result.quarters_required} {px.quartersRequired}</span>
                  </p>
                  <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">{px.pointsLabel}: {Number(result.total_agirc_arrco_points).toFixed(1)} pts</p>
                </div>

                <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4">
                  <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.rateLabel}</p>
                  <p className={`text-lg font-semibold mt-1 ${result.planned.achieves_full_rate ? "text-success" : "text-danger"}`}>
                    {formatPct(Number(result.planned.rate_applied) * 100, 2)}
                  </p>
                  <div className="mt-0.5"><RowBadge row={result.planned} /></div>
                </div>

                <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4">
                  <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.monthlyLabel}</p>
                  <p className="text-lg font-semibold mt-1 money text-slate-900 dark:text-foreground">
                    {formatMoney(result.planned.monthly_total)}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">
                    {px.replacementLabel}: {formatPct(Number(result.planned.replacement_ratio) * 100, 1)}
                  </p>
                </div>
              </div>

              {/* Breakdown */}
              <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-4">
                <h2 className="text-xs font-semibold text-slate-500 dark:text-muted-foreground uppercase tracking-wide mb-3">{px.monthlyLabel}</h2>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.regimeLabel}</p>
                    <p className="text-base font-semibold money text-slate-800 dark:text-foreground mt-0.5">
                      {formatMoney(result.planned.monthly_base)}
                    </p>
                  </div>
                  <div className="w-px bg-surface-border dark:bg-border" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.complementaryLabel}</p>
                    <p className="text-base font-semibold money text-slate-800 dark:text-foreground mt-0.5">
                      {formatMoney(result.planned.monthly_complementary)}
                    </p>
                  </div>
                  <div className="w-px bg-surface-border dark:bg-border" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-muted-foreground">{px.replacementLabel}</p>
                    <p className="text-base font-semibold text-slate-800 dark:text-foreground mt-0.5">
                      {formatPct(Number(result.planned.replacement_ratio) * 100, 1)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Interpretation */}
              {interpretation && (
                <div className="bg-brand-50 dark:bg-indigo-950/30 rounded-xl border border-brand/20 dark:border-indigo-800/30 p-4">
                  <p className="text-xs font-semibold text-brand dark:text-indigo-400 mb-1">{px.interpretation}</p>
                  <p className="text-sm text-slate-700 dark:text-foreground">{interpretation}</p>
                </div>
              )}

              {/* Sensitivity table */}
              <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
                <div className="px-4 py-3 border-b border-surface-border dark:border-border">
                  <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{px.sensitivityTitle}</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-secondary/50">
                        <th className="text-left px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.age}</th>
                        <th className="text-left px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.year}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.quarters}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.rate}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.regimeLabel}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.complementaryLabel}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.monthly}</th>
                        <th className="text-right px-3 py-2 text-xs font-medium text-slate-500 dark:text-muted-foreground">{px.replacement}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.sensitivity.map((row) => {
                        const isPlanned = row.retirement_year === parseInt(form.planned_retirement_year);
                        const isDecote = !row.achieves_full_rate;
                        const isSurcote = row.surcote_quarters > 0;

                        const rowClass = [
                          "border-t border-surface-border dark:border-border transition-colors",
                          isPlanned
                            ? "bg-brand-50 dark:bg-indigo-950/40 font-semibold"
                            : isDecote
                            ? "bg-red-50/60 dark:bg-red-950/20"
                            : isSurcote
                            ? "bg-blue-50/60 dark:bg-blue-950/20"
                            : "bg-green-50/40 dark:bg-green-950/10",
                        ].join(" ");

                        const rateColor = isDecote
                          ? "text-danger"
                          : isSurcote
                          ? "text-blue-600 dark:text-blue-400"
                          : "text-success";

                        return (
                          <tr key={row.retirement_year} className={rowClass}>
                            <td className="px-3 py-2 text-slate-700 dark:text-foreground">
                              {row.retirement_age}
                              {isPlanned && <span className="ml-1.5 text-xs text-brand dark:text-indigo-400">({px.planned})</span>}
                            </td>
                            <td className="px-3 py-2 text-slate-700 dark:text-foreground">{row.retirement_year}</td>
                            <td className="px-3 py-2 text-right text-slate-700 dark:text-foreground">
                              {row.quarters_validated}
                              <span className="text-slate-400 dark:text-muted-foreground text-xs"> / {result.quarters_required}</span>
                            </td>
                            <td className={`px-3 py-2 text-right ${rateColor}`}>
                              <span>{formatPct(Number(row.rate_applied) * 100, 2)}</span>
                              <span className="ml-1"><RowBadge row={row} /></span>
                            </td>
                            <td className="px-3 py-2 text-right money text-slate-700 dark:text-foreground">
                              {formatMoney(row.monthly_base)}
                            </td>
                            <td className="px-3 py-2 text-right money text-slate-700 dark:text-foreground">
                              {formatMoney(row.monthly_complementary)}
                            </td>
                            <td className="px-3 py-2 text-right money font-medium text-slate-900 dark:text-foreground">
                              {formatMoney(row.monthly_total)}
                            </td>
                            <td className="px-3 py-2 text-right text-slate-600 dark:text-muted-foreground">
                              {formatPct(Number(row.replacement_ratio) * 100, 1)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Disclaimer */}
              <p className="text-xs text-slate-400 dark:text-muted-foreground text-center pb-2">{px.disclaimer}</p>
            </div>
          ) : (
            <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-10 flex items-center justify-center min-h-[200px]">
              <p className="text-sm text-slate-400 dark:text-muted-foreground text-center">{px.noResult}</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
