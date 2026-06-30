"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, getLocale } from "@/lib/format/money";

interface MonthBucket {
  month: string;   // "YYYY-MM"
  spent: number;
  income: number;
}

function monthLabel(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  if (!y || !m) return ym;
  return new Date(y, m - 1, 1).toLocaleDateString(getLocale(), { month: "short" });
}

export function SpendingTrendChart({ data, title }: { data: MonthBucket[]; title: string }) {
  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) =>
        `${params[0].axisValue}<br/>${params
          .map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`)
          .join("<br/>")}`,
    },
    grid: { left: 60, right: 16, top: 16, bottom: 28 },
    xAxis: {
      type: "category",
      data: data.map((d) => monthLabel(d.month)),
      axisLabel: { fontSize: 11, color: "#94a3b8" },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.18)" } },
      axisLabel: {
        fontSize: 11,
        color: "#94a3b8",
        formatter: (val: number) => formatMoney(val),
      },
    },
    series: [
      {
        name: title,
        type: "bar",
        data: data.map((d) => d.spent),
        itemStyle: { color: "#2563eb", borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 48,
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{title}</h3>
      <ReactECharts option={option} style={{ height: 240 }} />
    </div>
  );
}
