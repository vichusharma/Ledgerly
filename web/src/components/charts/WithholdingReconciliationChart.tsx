"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatCompact } from "@/lib/format/money";

interface Props {
  title: string;
  estimatedTaxLabel: string;
  pasWithheldLabel: string;
  estimatedTax: number;
  pasWithheldProjected: number;
}

export function WithholdingReconciliationChart({
  title, estimatedTaxLabel, pasWithheldLabel, estimatedTax, pasWithheldProjected,
}: Props) {
  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (ps: any[]) => ps.map((p: any) => `${p.name}: ${formatMoney(p.value)}`).join("<br/>"),
    },
    grid: { left: 64, right: 24, top: 16, bottom: 24 },
    xAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)" } },
      axisLabel: { fontSize: 11, color: "#94a3b8", formatter: (v: number) => formatCompact(v) },
    },
    yAxis: {
      type: "category",
      data: [pasWithheldLabel, estimatedTaxLabel],
      axisLabel: { fontSize: 12, color: "#64748b" },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.3)" } },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: [
          { value: pasWithheldProjected, itemStyle: { color: "#94a3b8" } },
          { value: estimatedTax, itemStyle: { color: "#6366f1" } },
        ],
        barWidth: 28,
        itemStyle: { borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: "right",
          color: "#64748b",
          fontSize: 12,
          formatter: (p: any) => formatMoney(p.value),
        },
      },
    ],
  };

  return (
    <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{title}</h3>
      <ReactECharts option={option} style={{ height: 140 }} />
    </div>
  );
}
