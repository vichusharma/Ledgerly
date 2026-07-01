"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatPct } from "@/lib/format/money";

interface Slice { asset_class: string; market_value: number; actual_pct: number }

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

export function AllocationDonut({ slices, title }: { slices: Slice[]; title: string }) {
  const option = {
    tooltip: {
      formatter: (p: any) => `${p.name}<br/>${formatMoney(p.data.value)}<br/>${formatPct(p.percent)}`,
    },
    series: [
      {
        type: "pie",
        radius: ["55%", "75%"],
        avoidLabelOverlap: false,
        label: { show: false },
        data: slices.map((s, i) => ({
          name: s.asset_class,
          value: s.market_value,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
      },
    ],
  };

  return (
    <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{title}</h3>
      <div className="flex items-center gap-4">
        <ReactECharts option={option} style={{ height: 150, width: 150, flexShrink: 0 }} />
        <div className="flex-1 space-y-2 min-w-0">
          {slices.map((s, i) => (
            <div key={s.asset_class} className="flex items-center gap-2 text-xs">
              <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
              <span className="text-slate-700 dark:text-foreground truncate flex-1">{s.asset_class}</span>
              <span className="money text-slate-400 dark:text-muted-foreground">{formatPct(s.actual_pct)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
