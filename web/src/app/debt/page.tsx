"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { useLoans, useLoanSchedule, useLoanSummary } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";

export default function DebtPage() {
  const { data: loans = [] } = useLoans();
  const [selectedLoan, setSelectedLoan] = useState<number | null>(null);
  const loanId = selectedLoan ?? loans[0]?.id;
  const { t } = useLanguage();
  const dx = t("debt");

  const { data: summary } = useLoanSummary(loanId);
  const { data: schedule = [] } = useLoanSchedule(loanId);

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{dx.title}</h1>

        {/* Loan selector */}
        {loans.length > 1 && (
          <div className="flex gap-2">
            {loans.map((l: any) => (
              <button
                key={l.id}
                onClick={() => setSelectedLoan(l.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                  loanId === l.id
                    ? "bg-brand border-brand text-white"
                    : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                }`}
              >
                {l.name}
              </button>
            ))}
          </div>
        )}

        {/* Summary KPIs */}
        {summary && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard title={dx.remainingCapital} value={formatMoney(summary.remaining_capital)} trend={-1} />
            <KpiCard title={dx.interestYtd} value={formatMoney(summary.interest_paid_ytd)} />
            <KpiCard title={dx.interestTotal} value={formatMoney(summary.interest_paid_total)} />
            <KpiCard
              title={dx.nextPayment}
              value={summary.next_payment_amount ? formatMoney(summary.next_payment_amount) : "—"}
              subtitle={summary.next_payment_date ? formatDate(summary.next_payment_date) : undefined}
            />
          </div>
        )}

        {/* Amortization table */}
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
          <div className="px-5 py-4 border-b border-surface-border dark:border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{dx.schedule}</h3>
            <span className="text-xs text-slate-400 dark:text-muted-foreground">{schedule.length} {dx.payments}</span>
          </div>
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white dark:bg-card">
                <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border">
                  {[dx.period, dx.date, dx.payment, dx.principal, dx.interest, dx.balance].map(h => (
                    <th key={h} className="px-4 py-2 text-right first:text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {schedule.map((row: any) => (
                  <tr key={row.period} className="border-b border-slate-50 dark:border-border hover:bg-slate-50 dark:hover:bg-secondary">
                    <td className="px-4 py-2 text-slate-400 dark:text-muted-foreground text-xs">{row.period}</td>
                    <td className="px-4 py-2 money text-slate-500 dark:text-muted-foreground text-right">{formatDate(row.payment_date)}</td>
                    <td className="px-4 py-2 money text-slate-700 dark:text-foreground text-right font-medium">{formatMoney(row.payment)}</td>
                    <td className="px-4 py-2 money text-slate-600 dark:text-foreground text-right">{formatMoney(row.principal)}</td>
                    <td className="px-4 py-2 money text-danger text-right">{formatMoney(row.interest)}</td>
                    <td className="px-4 py-2 money text-slate-500 dark:text-muted-foreground text-right">{formatMoney(row.balance)}</td>
                  </tr>
                ))}
                {schedule.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground text-sm">
                      {dx.noLoans}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
