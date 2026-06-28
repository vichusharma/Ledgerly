"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney } from "@/lib/format/money";

interface DataPoint {
  date: string;
  net_worth: number;
  assets: number;
  liabilities: number;
}

export function NetWorthChart({ data }: { data: DataPoint[] }) {
  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any[]) =>
        params
          .map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`)
          .join("<br/>"),
    },
    legend: {
      data: ["Patrimoine net", "Actifs", "Dettes"],
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
        name: "Patrimoine net",
        type: "line",
        data: data.map((d) => d.net_worth),
        smooth: true,
        lineStyle: { width: 2.5, color: "#2563eb" },
        areaStyle: { color: "rgba(37,99,235,0.08)" },
        symbol: "none",
      },
      {
        name: "Actifs",
        type: "line",
        data: data.map((d) => d.assets),
        smooth: true,
        lineStyle: { width: 1.5, color: "#10b981", type: "dashed" },
        symbol: "none",
      },
      {
        name: "Dettes",
        type: "line",
        data: data.map((d) => d.liabilities),
        smooth: true,
        lineStyle: { width: 1.5, color: "#ef4444", type: "dashed" },
        symbol: "none",
      },
    ],
  };

  return (
    <div className="bg-white rounded-xl border border-surface-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">Évolution du patrimoine</h3>
      <ReactECharts option={option} style={{ height: 280 }} />
    </div>
  );
}
