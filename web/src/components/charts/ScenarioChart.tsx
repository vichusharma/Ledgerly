"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney } from "@/lib/format/money";

interface SeriesPoint {
  month: number;
  invest: number;
  prepay: number;
}

interface Props {
  series: SeriesPoint[];
  breakeven_month?: number | null;
  label: string;
}

export function ScenarioChart({ series, breakeven_month, label }: Props) {
  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) => {
        const month = params[0]?.axisValue;
        return [
          `<b>Mois ${month}</b>`,
          ...params.map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`),
        ].join("<br/>");
      },
    },
    legend: { data: ["Investir", "Rembourser"], bottom: 0 },
    grid: { left: 70, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: "category",
      data: series.map((p) => p.month),
      name: "Mois",
      nameLocation: "end",
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: (v: number) => formatMoney(v) },
    },
    markLine: breakeven_month
      ? {
          data: [
            {
              xAxis: breakeven_month,
              label: { formatter: `Seuil M${breakeven_month}` },
              lineStyle: { color: "#10b981", type: "dashed" },
            },
          ],
        }
      : undefined,
    series: [
      {
        name: "Investir",
        type: "line",
        data: series.map((p) => p.invest),
        smooth: true,
        lineStyle: { color: "#2563eb", width: 2 },
        symbol: "none",
      },
      {
        name: "Rembourser",
        type: "line",
        data: series.map((p) => p.prepay),
        smooth: true,
        lineStyle: { color: "#f59e0b", width: 2 },
        symbol: "none",
      },
    ],
  };

  return (
    <div className="bg-white rounded-xl border border-surface-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-1">
        Scénario — {label}
      </h3>
      {breakeven_month && (
        <p className="text-xs text-success mb-3">
          ✓ Investir devient plus rentable au mois {breakeven_month}
        </p>
      )}
      <ReactECharts option={option} style={{ height: 300 }} />
    </div>
  );
}
