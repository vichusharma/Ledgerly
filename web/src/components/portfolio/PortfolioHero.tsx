"use client";

import { TrendingUp, TrendingDown } from "lucide-react";
import { formatMoney, formatPct } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

export function PortfolioHero({
  currentValue, gainLoss, gainPct,
}: { currentValue: number; gainLoss: number; gainPct: number }) {
  const { t } = useLanguage();
  const px = t("portfolio");
  const up = gainLoss >= 0;

  return (
    <div className="h-full flex flex-col justify-between bg-white dark:bg-card bg-gradient-to-br from-brand/[0.06] via-transparent to-transparent rounded-xl border border-surface-border dark:border-border shadow-sm p-6">
      <div>
        <p className="text-xs font-medium text-slate-500 dark:text-muted-foreground uppercase tracking-wider">{px.currentValue}</p>
        <p className="mt-2 text-4xl lg:text-5xl font-semibold text-slate-900 dark:text-foreground money tracking-tight leading-none">
          {formatMoney(currentValue)}
        </p>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
              up ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
            }`}
          >
            {up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {formatPct(Math.abs(gainPct))}
          </span>
          <span className="text-xs text-slate-400 dark:text-muted-foreground">
            {up ? "+" : "−"}{formatMoney(Math.abs(gainLoss))} {px.gainLossLabel}
          </span>
        </div>
      </div>
    </div>
  );
}
