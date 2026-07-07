"use client";

import { formatDate } from "@/lib/format/money";

interface Props {
  name: string;
  arrivalDate: string | null;
  yearsRemaining: number | null;
  tx: Record<string, string>;
}

const TOTAL_YEARS = 8;

export function ImpatriateTimeline({ name, arrivalDate, yearsRemaining, tx }: Props) {
  const expired = yearsRemaining === 0;
  const elapsed = yearsRemaining == null ? TOTAL_YEARS : Math.max(0, TOTAL_YEARS - yearsRemaining);
  const pct = Math.min(100, (elapsed / TOTAL_YEARS) * 100);

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-foreground">{name}</h4>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          expired ? "bg-danger/10 text-danger" : "bg-brand/10 text-brand"
        }`}>
          {expired
            ? tx.impatriateExpired
            : `${yearsRemaining} ${tx.impatriateYearsRemaining}`}
        </span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 dark:bg-secondary overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${expired ? "bg-danger" : "bg-brand"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between mt-1.5 text-xs text-slate-400 dark:text-muted-foreground">
        <span>{arrivalDate ? formatDate(arrivalDate) : "—"}</span>
        <span>{TOTAL_YEARS} {tx.impatriateYearsTotal}</span>
      </div>
    </div>
  );
}
