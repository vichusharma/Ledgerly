"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface DataPoint {
  date: string;
  net_worth: number;
  assets: number;
  liabilities: number;
}

export function NetWorthChart({ data }: { data: DataPoint[] }) {
  const { t } = useLanguage();
  const dx = t("dashboard");

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) =>
        params
          .map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`)
          .join("<br/>"),
    },
    legend: {
      data: [dx.netWorth, dx.assets, dx.liabilities],
      bottom: 0,
    },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: "category",
      data: data.map((d) => d.date),
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        fontSize: 11,
        formatter: (val: number) => formatMoney(val),
      },
    },
    series: [
      {
        name: dx.netWorth,
        type: "line",
        data: data.map((d) => d.net_worth),
        smooth: true,
        lineStyle: { width: 2.5, color: "#2563eb" },
        areaStyle: { color: "rgba(37,99,235,0.08)" },
        symbol: "none",
      },
      {
        name: dx.assets,
        type: "line",
        data: data.map((d) => d.assets),
        smooth: true,
        lineStyle: { width: 1.5, color: "#10b981", type: "dashed" },
        symbol: "none",
      },
      {
        name: dx.liabilities,
        type: "line",
        data: data.map((d) => d.liabilities),
        smooth: true,
        lineStyle: { width: 1.5, color: "#ef4444", type: "dashed" },
        symbol: "none",
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{dx.evolution}</h3>
      <ReactECharts option={option} style={{ height: 280 }} />
    </div>
  );
}
