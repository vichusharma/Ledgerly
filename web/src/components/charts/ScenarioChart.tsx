"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

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
  const { t } = useLanguage();
  const sx = t("scenarios");

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) => {
        const month = params[0]?.axisValue;
        return [
          `<b>${sx.month} ${month}</b>`,
          ...params.map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`),
        ].join("<br/>");
      },
    },
    legend: { data: [sx.invest, sx.prepay], bottom: 0 },
    grid: { left: 70, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: "category",
      data: series.map((p) => p.month),
      name: sx.month,
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
              label: { formatter: `${sx.threshold} M${breakeven_month}` },
              lineStyle: { color: "#10b981", type: "dashed" },
            },
          ],
        }
      : undefined,
    series: [
      {
        name: sx.invest,
        type: "line",
        data: series.map((p) => p.invest),
        smooth: true,
        lineStyle: { color: "#2563eb", width: 2 },
        symbol: "none",
      },
      {
        name: sx.prepay,
        type: "line",
        data: series.map((p) => p.prepay),
        smooth: true,
        lineStyle: { color: "#f59e0b", width: 2 },
        symbol: "none",
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-1">
        {sx.chartTitle} — {label}
      </h3>
      {breakeven_month && (
        <p className="text-xs text-success mb-3">
          ✓ {sx.breakevenText} {breakeven_month}
        </p>
      )}
      <ReactECharts option={option} style={{ height: 300 }} />
    </div>
  );
}
