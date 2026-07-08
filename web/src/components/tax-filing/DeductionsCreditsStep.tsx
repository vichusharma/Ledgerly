"use client";

import { useEffect } from "react";
import { useComputeFiling, useFilingSnapshot } from "@/lib/api/hooks";
import { formatMoney } from "@/lib/format/money";

interface Tf { [key: string]: string }

export function DeductionsCreditsStep({ year, tf }: { year: number; tf: Tf }) {
  const { data: snapshot, isError } = useFilingSnapshot(year);
  const compute = useComputeFiling();

  useEffect(() => {
    if (isError) {
      compute.mutate(year);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isError, year]);

  const payload = snapshot?.payload;
  const lines = payload?.lines_2047 ?? [];

  const methodLabel = (method: string) =>
    method === "exemption_with_effective_rate" ? tf.methodExemption : tf.methodCredit;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tf.deductionsTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{tf.deductionsDesc}</p>
      </div>

      <button
        onClick={() => compute.mutate(year)}
        disabled={compute.isPending}
        className="bg-brand text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50 hover:bg-brand-700 w-fit"
      >
        {tf.recompute}
      </button>

      {lines.length === 0 ? (
        <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.noForeignIncomeLines}</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-400 dark:text-muted-foreground text-left">
              <th className="py-1.5 font-medium">{tf.country}</th>
              <th className="py-1.5 font-medium">{tf.description}</th>
              <th className="py-1.5 font-medium text-right">{tf.grossAmount}</th>
              <th className="py-1.5 font-medium">{tf.methodOverride}</th>
              <th className="py-1.5 font-medium text-right">{tf.creditOrExemption}</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line: any, i: number) => (
              <tr key={i} className="border-t border-surface-border dark:border-border">
                <td className="py-1.5">{line.source_country_code}</td>
                <td className="py-1.5">{line.source_description}</td>
                <td className="py-1.5 text-right money">{formatMoney(line.gross_amount_eur)}</td>
                <td className="py-1.5">{methodLabel(line.elimination_method)}</td>
                <td className="py-1.5 text-right money">{formatMoney(line.french_tax_credit_or_exemption)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.methodOverrideHint}</p>
    </div>
  );
}
