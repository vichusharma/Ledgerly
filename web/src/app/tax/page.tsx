"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useTaxEstimate } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { KpiCard } from "@/components/finance/KpiCard";
import { WithholdingReconciliationChart } from "@/components/charts/WithholdingReconciliationChart";
import { ImpatriateTimeline } from "@/components/charts/ImpatriateTimeline";
import { formatMoney, formatDate } from "@/lib/format/money";

export default function TaxPage() {
  const { t } = useLanguage();
  const tx = t("tax");

  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState<number>(currentYear);
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  const { data: estimate, isLoading, isError } = useTaxEstimate(year);

  const inputCls = "mt-1 text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const labelCls = "block text-xs text-slate-500 dark:text-muted-foreground font-medium";
  const cardCls = "bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5";

  const balance = estimate ? Number(estimate.balance) : 0;
  const owes = balance > 0;

  const impatriatePersons = (estimate?.persons ?? []).filter((p: any) => p.impatriate_enabled);

  return (
    <AppShell>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{tx.title}</h1>
            <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{tx.subtitle}</p>
          </div>
          <div>
            <label className={labelCls}>{tx.year}</label>
            <select value={year} onChange={(e) => setYear(Number(e.target.value))} className={inputCls}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {isLoading && (
          <div className={`${cardCls} p-10 flex items-center justify-center`}>
            <p className="text-sm text-slate-400 dark:text-muted-foreground">{tx.loading}</p>
          </div>
        )}

        {isError && (
          <div className={`${cardCls} p-10 flex items-center justify-center`}>
            <p className="text-sm text-danger">{tx.error}</p>
          </div>
        )}

        {estimate && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <KpiCard title={tx.kpiEstimatedTax} value={formatMoney(estimate.estimated_tax)} />
              <KpiCard
                title={tx.kpiPasWithheld}
                value={formatMoney(estimate.pas_withheld_projected_annual_total)}
                subtitle={`${tx.pasWithheldYtd}: ${formatMoney(estimate.pas_withheld_ytd_total)}`}
              />
              <KpiCard
                title={tx.kpiBalance}
                value={formatMoney(Math.abs(balance))}
                trend={owes ? -1 : 1}
                subtitle={owes ? tx.balanceOwe : tx.balanceRefund}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <WithholdingReconciliationChart
                title={tx.chartTitle}
                estimatedTaxLabel={tx.kpiEstimatedTax}
                pasWithheldLabel={tx.kpiPasWithheld}
                estimatedTax={Number(estimate.estimated_tax)}
                pasWithheldProjected={Number(estimate.pas_withheld_projected_annual_total)}
              />

              <div className={cardCls}>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-3">{tx.householdSummaryTitle}</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-500 dark:text-muted-foreground">{tx.filingStatusLabel}</dt>
                    <dd className="text-slate-800 dark:text-foreground font-medium">
                      {estimate.filing_status === "married_pacs" ? tx.filingStatusMarriedPacs : tx.filingStatusSingle}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500 dark:text-muted-foreground">{tx.partsLabel}</dt>
                    <dd className="text-slate-800 dark:text-foreground font-medium">
                      {estimate.parts != null ? Number(estimate.parts) : tx.partsNotApplicable}
                    </dd>
                  </div>
                  <div className="flex justify-between border-t border-surface-border dark:border-border pt-2">
                    <dt className="text-slate-500 dark:text-muted-foreground">{tx.householdGross}</dt>
                    <dd className="money text-slate-800 dark:text-foreground font-medium">
                      {formatMoney(estimate.household_gross_income_projected)}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500 dark:text-muted-foreground">{tx.householdTaxable}</dt>
                    <dd className="money text-slate-800 dark:text-foreground font-medium">
                      {formatMoney(estimate.household_taxable_income_projected)}
                    </dd>
                  </div>
                  {estimate.quotient_familial_capped && (
                    <p className="text-xs text-amber-600 dark:text-amber-400 pt-1">{tx.plafonnementApplied}</p>
                  )}
                </dl>
              </div>
            </div>

            <div className={`${cardCls} overflow-hidden !p-0`}>
              <div className="px-5 py-4 border-b border-surface-border dark:border-border">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tx.personBreakdownTitle}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-secondary border-b border-surface-border dark:border-border text-slate-400 dark:text-muted-foreground">
                      <th className="px-4 py-2 text-left font-medium">{tx.colName}</th>
                      <th className="px-4 py-2 text-right font-medium">{tx.colGross}</th>
                      <th className="px-4 py-2 text-right font-medium">{tx.colNetTaxable}</th>
                      <th className="px-4 py-2 text-right font-medium">{tx.colNetTaxableAfterImpatriate}</th>
                      <th className="px-4 py-2 text-right font-medium">{tx.colParts}</th>
                      <th className="px-4 py-2 text-right font-medium">{tx.colPasProjected}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {estimate.persons.map((p: any) => (
                      <tr key={p.person_id} className="border-b border-slate-50 dark:border-border">
                        <td className="px-4 py-2.5 text-slate-700 dark:text-foreground">{p.name}</td>
                        <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">
                          {p.has_payslip_data ? formatMoney(p.gross_annual_projected) : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">
                          {p.has_payslip_data ? formatMoney(p.net_taxable_annual_projected) : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">
                          {p.has_payslip_data ? formatMoney(p.net_taxable_after_impatriate) : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right text-slate-700 dark:text-foreground">
                          {Number(p.parts_used)}
                        </td>
                        <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">
                          {p.has_payslip_data ? formatMoney(p.pas_withheld_projected_annual) : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {impatriatePersons.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-3">{tx.impatriateSectionTitle}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {impatriatePersons.map((p: any) => (
                    <ImpatriateTimeline
                      key={p.person_id}
                      name={p.name}
                      arrivalDate={p.impatriate_arrival_date}
                      yearsRemaining={p.impatriate_years_remaining}
                      tx={tx}
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="bg-slate-50 dark:bg-secondary/40 rounded-xl border border-surface-border dark:border-border p-4">
              <p className="text-xs font-semibold text-slate-500 dark:text-muted-foreground mb-2">{tx.simplificationsTitle}</p>
              <ul className="text-xs text-slate-500 dark:text-muted-foreground space-y-1 list-disc list-inside">
                {estimate.simplifications_applied.map((key: string) => (
                  <li key={key}>{(tx as Record<string, string>)[`simplification_${key}`] ?? key}</li>
                ))}
              </ul>
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-3">{tx.disclaimer}</p>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
