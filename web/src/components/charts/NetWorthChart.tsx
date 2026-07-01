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
      textStyle: { color: "#94a3b8", fontSize: 11 },
      icon: "roundRect",
      itemWidth: 10,
      itemHeight: 10,
    },
    grid: { left: 60, right: 20, top: 16, bottom: 44 },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: data.map((d) => d.date),
      axisLabel: { fontSize: 11, color: "#94a3b8" },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.3)" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)" } },
      axisLabel: {
        fontSize: 11,
        color: "#94a3b8",
        formatter: (val: number) => formatMoney(val),
      },
    },
    series: [
      {
        name: dx.netWorth,
        type: "line",
        data: data.map((d) => d.net_worth),
        smooth: true,
        lineStyle: { width: 3, color: "#6366f1" },
        itemStyle: { color: "#6366f1" },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(99,102,241,0.28)" },
              { offset: 1, color: "rgba(99,102,241,0)" },
            ],
          },
        },
        symbol: "none",
        z: 3,
      },
      {
        name: dx.assets,
        type: "line",
        data: data.map((d) => d.assets),
        smooth: true,
        lineStyle: { width: 1.5, color: "#10b981", type: "dashed" },
        itemStyle: { color: "#10b981" },
        symbol: "none",
      },
      {
        name: dx.liabilities,
        type: "line",
        data: data.map((d) => d.liabilities),
        smooth: true,
        lineStyle: { width: 1.5, color: "#ef4444", type: "dashed" },
        itemStyle: { color: "#ef4444" },
        symbol: "none",
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{dx.evolution}</h3>
      <ReactECharts option={option} style={{ height: 300 }} />
    </div>
  );
}
