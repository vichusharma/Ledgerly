"use client";

import { TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: number;   // positive = green, negative = red
  className?: string;
}

export function KpiCard({ title, value, subtitle, trend, className }: KpiCardProps) {
  const hasTrend = trend !== undefined;
  const up = (trend ?? 0) >= 0;
  return (
    <div className={cn("bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5", className)}>
      <p className="text-xs font-medium text-slate-500 dark:text-muted-foreground uppercase tracking-wider">{title}</p>
      <p className="mt-1.5 text-2xl font-semibold text-slate-900 dark:text-foreground money tracking-tight">{value}</p>
      {subtitle && (
        <div className="mt-2">
          {hasTrend ? (
            <span className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
              up ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
            )}>
              {up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {subtitle}
            </span>
          ) : (
            <p className="text-xs text-slate-400 dark:text-muted-foreground">{subtitle}</p>
          )}
        </div>
      )}
    </div>
  );
}
