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
  return (
    <div className={cn("bg-white rounded-xl border border-surface-border p-5", className)}>
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900 money">{value}</p>
      {(subtitle || trend !== undefined) && (
        <div className="mt-1 flex items-center gap-1">
          {trend !== undefined && (
            trend >= 0 ? (
              <TrendingUp className="h-3 w-3 text-success" />
            ) : (
              <TrendingDown className="h-3 w-3 text-danger" />
            )
          )}
          {subtitle && (
            <p className={cn(
              "text-xs",
              trend === undefined ? "text-slate-400" :
              trend >= 0 ? "text-success" : "text-danger"
            )}>
              {subtitle}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
