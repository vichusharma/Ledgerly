"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { useLoans, useLoanSchedule, useLoanSummary } from "@/lib/api/hooks";
import { formatMoney, formatDate } from "@/lib/format/money";

export default function DebtPage() {
  const { data: loans = [] } = useLoans();
  const [selectedLoan, setSelectedLoan] = useState<number | null>(null);
  const loanId = selectedLoan ?? loans[0]?.id;

  const { data: summary } = useLoanSummary(loanId);
  const { data: schedule = [] } = useLoanSchedule(loanId);

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900">Crédits</h1>

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
                    : "border-surface-border text-slate-600 hover:bg-slate-50"
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
            <KpiCard
              title="Capital restant"
              value={formatMoney(summary.remaining_capital)}
              trend={-1}
            />
            <KpiCard
              title="Intérêts payés (YTD)"
              value={formatMoney(summary.interest_paid_ytd)}
            />
            <KpiCard
              title="Intérêts payés (total)"
              value={formatMoney(summary.interest_paid_total)}
            />
            <KpiCard
              title="Prochaine échéance"
              value={summary.next_payment_amount ? formatMoney(summary.next_payment_amount) : "—"}
              subtitle={summary.next_payment_date ? formatDate(summary.next_payment_date) : undefined}
            />
          </div>
        )}

        {/* Amortization table */}
        <div className="bg-white rounded-xl border border-surface-border overflow-hidden">
          <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">Tableau d'amortissement</h3>
            <span className="text-xs text-slate-400">{schedule.length} échéances</span>
          </div>
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white">
                <tr className="text-xs text-slate-400 border-b border-surface-border">
                  {["N°", "Date", "Mensualité", "Principal", "Intérêts", "Capital restant"].map(h => (
                    <th key={h} className="px-4 py-2 text-right first:text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {schedule.map((row: any) => (
                  <tr key={row.period} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="px-4 py-2 text-slate-400 text-xs">{row.period}</td>
                    <td className="px-4 py-2 money text-slate-500 text-right">{formatDate(row.payment_date)}</td>
                    <td className="px-4 py-2 money text-slate-700 text-right font-medium">{formatMoney(row.payment)}</td>
                    <td className="px-4 py-2 money text-slate-600 text-right">{formatMoney(row.principal)}</td>
                    <td className="px-4 py-2 money text-danger text-right">{formatMoney(row.interest)}</td>
                    <td className="px-4 py-2 money text-slate-500 text-right">{formatMoney(row.balance)}</td>
                  </tr>
                ))}
                {schedule.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400 text-sm">
                      Aucun crédit — ajoutez-en un via Paramètres
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
