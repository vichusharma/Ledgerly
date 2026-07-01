"use client";

import ReactECharts from "echarts-for-react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { formatMoney, formatPct } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface SeriesPoint { date: string; net_worth: number }

export function NetWorthHero({ current, series }: { current: number; series: SeriesPoint[] }) {
  const { t } = useLanguage();
  const dx = t("dashboard");

  const first = series[0]?.net_worth ?? current;
  const last = series.length ? series[series.length - 1].net_worth : current;
  const delta = last - first;
  const pct = first ? (delta / Math.abs(first)) * 100 : 0;
  const up = delta >= 0;

  const spark = {
    grid: { left: 0, right: 0, top: 6, bottom: 0 },
    xAxis: { type: "category", show: false, boundaryGap: false, data: series.map((s) => s.date) },
    yAxis: { type: "value", show: false, scale: true },
    tooltip: { show: false },
    series: [
      {
        type: "line",
        smooth: true,
        symbol: "none",
        data: series.map((s) => s.net_worth),
        lineStyle: { width: 2.5, color: "#818cf8" },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(99,102,241,0.35)" },
              { offset: 1, color: "rgba(99,102,241,0)" },
            ],
          },
        },
      },
    ],
  };

  return (
    <div className="h-full flex flex-col justify-between bg-white dark:bg-card bg-gradient-to-br from-brand/[0.06] via-transparent to-transparent rounded-xl border border-surface-border dark:border-border shadow-sm p-6">
      <div>
        <p className="text-xs font-medium text-slate-500 dark:text-muted-foreground uppercase tracking-wider">{dx.netWorth}</p>
        <p className="mt-2 text-4xl lg:text-5xl font-semibold text-slate-900 dark:text-foreground money tracking-tight leading-none">
          {formatMoney(current)}
        </p>
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
              up ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
            }`}
          >
            {up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {formatPct(Math.abs(pct))}
          </span>
          <span className="text-xs text-slate-400 dark:text-muted-foreground">
            {up ? "+" : "−"}{formatMoney(Math.abs(delta))} {dx.thisYear}
          </span>
        </div>
      </div>
      {series.length > 1 && <ReactECharts option={spark} style={{ height: 56 }} className="mt-4" />}
    </div>
  );
}
