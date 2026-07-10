"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import {
  useLoans, useLoanSchedule, useLoanSummary, usePreviewPrepayment, useApplyPrepayment,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function ScenarioCard({
  title, scenario, dx, onChoose,
}: { title: string; scenario: any; dx: any; onChoose: () => void }) {
  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-4 space-y-2">
      <h4 className="text-sm font-semibold text-slate-700 dark:text-foreground">{title}</h4>
      <dl className="text-sm space-y-1">
        <div className="flex justify-between">
          <dt className="text-slate-400 dark:text-muted-foreground">{dx.prepaySimNewPayment}</dt>
          <dd className="money font-medium text-slate-700 dark:text-foreground">{formatMoney(scenario.new_payment)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400 dark:text-muted-foreground">{dx.prepaySimNewPayoffDate}</dt>
          <dd className="money text-slate-700 dark:text-foreground">
            {scenario.payoff_date ? formatDate(scenario.payoff_date) : "—"}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400 dark:text-muted-foreground">{dx.prepaySimRemainingPeriods}</dt>
          <dd className="money text-slate-700 dark:text-foreground">{scenario.remaining_periods}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400 dark:text-muted-foreground">{dx.prepaySimInterestRemaining}</dt>
          <dd className="money text-slate-700 dark:text-foreground">{formatMoney(scenario.total_interest_remaining)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-400 dark:text-muted-foreground">{dx.prepaySimInterestSaved}</dt>
          <dd className="money font-medium text-success">{formatMoney(scenario.interest_saved_vs_baseline)}</dd>
        </div>
      </dl>
      <button
        onClick={onChoose}
        className="w-full bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700"
      >
        {dx.prepaySimChoose}
      </button>
    </div>
  );
}

export default function DebtPage() {
  const { data: loans = [] } = useLoans();
  const [selectedLoan, setSelectedLoan] = useState<number | null>(null);
  const loanId = selectedLoan ?? loans[0]?.id;
  const { t } = useLanguage();
  const dx = t("debt");

  const { data: summary } = useLoanSummary(loanId);
  const { data: schedule = [] } = useLoanSchedule(loanId);

  const previewPrepayment = usePreviewPrepayment();
  const applyPrepayment = useApplyPrepayment();

  const [amount, setAmount] = useState("");
  const [appliedDate, setAppliedDate] = useState(todayIso());
  const [preview, setPreview] = useState<any>(null);
  const [chosenMode, setChosenMode] = useState<"reduce_term" | "reduce_emi" | null>(null);
  const [simError, setSimError] = useState("");
  const [simMsg, setSimMsg] = useState("");

  const resetSimulator = () => {
    setAmount("");
    setPreview(null);
    setChosenMode(null);
    setSimError("");
  };

  const handlePreview = async () => {
    setSimError("");
    setSimMsg("");
    setChosenMode(null);
    try {
      const result = await previewPrepayment.mutateAsync({
        id: loanId, amount, reduction_mode: "term", applied_date: appliedDate,
      });
      setPreview(result);
    } catch {
      setSimError(dx.prepaySimError);
    }
  };

  const handleConfirm = async () => {
    if (!chosenMode || !preview) return;
    setSimError("");
    try {
      // Use the amount/date the preview was actually computed for (not the live
      // input state, which stays editable until the user starts over) so what
      // gets applied always matches what was reviewed.
      await applyPrepayment.mutateAsync({
        id: loanId,
        amount: preview.amount,
        reduction_mode: chosenMode === "reduce_term" ? "term" : "payment",
        applied_date: preview.as_of,
      });
      setSimMsg(dx.prepaySimApplied);
      resetSimulator();
    } catch {
      setSimError(dx.prepaySimError);
    }
  };

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

        {/* Prepayment simulator */}
        {loanId && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{dx.prepaySimTitle}</h3>

            {!chosenMode && (
              <div className="flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
                  {dx.prepaySimAmount}
                  <input
                    type="number"
                    value={amount}
                    disabled={!!preview}
                    onChange={(e) => setAmount(e.target.value)}
                    className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 money bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20 disabled:opacity-50"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs text-slate-400 dark:text-muted-foreground">
                  {dx.prepaySimDate}
                  <input
                    type="date"
                    value={appliedDate}
                    disabled={!!preview}
                    onChange={(e) => setAppliedDate(e.target.value)}
                    className="text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 bg-white dark:bg-secondary dark:text-foreground focus:outline-none focus:ring-2 focus:ring-brand/20 disabled:opacity-50"
                  />
                </label>
                {!preview ? (
                  <button
                    onClick={handlePreview}
                    disabled={!amount || previewPrepayment.isPending}
                    className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
                  >
                    {dx.prepaySimPreviewBtn}
                  </button>
                ) : (
                  <button
                    onClick={() => setPreview(null)}
                    className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
                  >
                    {dx.prepaySimCancelBtn}
                  </button>
                )}
              </div>
            )}

            {simError && <p className="text-xs text-danger">{simError}</p>}
            {simMsg && <p className="text-xs text-success">{simMsg}</p>}

            {preview && !chosenMode && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ScenarioCard
                  title={dx.prepaySimReduceTerm}
                  scenario={preview.reduce_term}
                  dx={dx}
                  onChoose={() => setChosenMode("reduce_term")}
                />
                <ScenarioCard
                  title={dx.prepaySimReduceEmi}
                  scenario={preview.reduce_emi}
                  dx={dx}
                  onChoose={() => setChosenMode("reduce_emi")}
                />
              </div>
            )}

            {chosenMode && (
              <div className="space-y-3">
                <p className="text-sm text-slate-700 dark:text-foreground">
                  {dx.prepaySimConfirmTitle} — {formatMoney(amount)} ({chosenMode === "reduce_term" ? dx.prepaySimReduceTerm : dx.prepaySimReduceEmi})
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleConfirm}
                    disabled={applyPrepayment.isPending}
                    className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
                  >
                    {dx.prepaySimConfirmBtn}
                  </button>
                  <button
                    onClick={() => setChosenMode(null)}
                    className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
                  >
                    {dx.prepaySimCancelBtn}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Amortization table */}
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm overflow-hidden">
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
