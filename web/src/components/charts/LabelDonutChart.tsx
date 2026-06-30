"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatPct } from "@/lib/format/money";

interface LabelBucket {
  label_id: number | null;
  name: string;
  color: string | null;
  spent: number;
  pct: number;
}

const COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316", "#64748b"];

const colorFor = (l: LabelBucket, i: number) => l.color || COLORS[i % COLORS.length];

export function LabelDonutChart({ data, title }: { data: LabelBucket[]; title: string }) {
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
        data: data.map((l, i) => ({
          name: l.name,
          value: l.spent,
          itemStyle: { color: colorFor(l, i) },
        })),
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{title}</h3>
      <div className="flex items-center gap-4">
        <ReactECharts option={option} style={{ height: 160, width: 160, flexShrink: 0 }} />
        <div className="flex-1 space-y-1.5 min-w-0">
          {data.slice(0, 6).map((l, i) => (
            <div key={l.label_id ?? l.name} className="flex items-center gap-2 text-xs">
              <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: colorFor(l, i) }} />
              <span className="text-slate-700 dark:text-foreground truncate flex-1">{l.name}</span>
              <span className="money text-slate-500 dark:text-muted-foreground whitespace-nowrap">{formatMoney(l.spent)}</span>
              <span className="money text-slate-400 dark:text-muted-foreground w-10 text-right">{formatPct(l.pct)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
