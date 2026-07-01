"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatCompact, getLocale } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface MonthBucket { month: string; spent: number; income: number }

function monthLabel(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  if (!y || !m) return ym;
  return new Date(y, m - 1, 1).toLocaleDateString(getLocale(), { month: "short" });
}

export function CashflowChart({ data, title }: { data: MonthBucket[]; title: string }) {
  const { t } = useLanguage();
  const dx = t("dashboard");
  const recent = data.slice(-6);
  const cur = recent[recent.length - 1];
  const net = cur ? cur.income - cur.spent : 0;

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (ps: any[]) =>
        `${ps[0].axisValue}<br/>${ps.map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`).join("<br/>")}`,
    },
    grid: { left: 52, right: 12, top: 12, bottom: 24 },
    xAxis: {
      type: "category",
      data: recent.map((d) => monthLabel(d.month)),
      axisLabel: { fontSize: 11, color: "#94a3b8" },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.3)" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)" } },
      axisLabel: { fontSize: 11, color: "#94a3b8", formatter: (v: number) => formatCompact(v) },
    },
    series: [
      { name: dx.inflow, type: "bar", data: recent.map((d) => d.income), itemStyle: { color: "#10b981", borderRadius: [3, 3, 0, 0] }, barMaxWidth: 18 },
      { name: dx.outflow, type: "bar", data: recent.map((d) => d.spent), itemStyle: { color: "#ef4444", borderRadius: [3, 3, 0, 0] }, barMaxWidth: 18 },
    ],
  };

  return (
    <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{title}</h3>
      <div className="flex items-baseline gap-2 mt-1 mb-3 flex-wrap">
        <span className={`text-xl font-semibold money ${net >= 0 ? "text-success" : "text-danger"}`}>
          {net >= 0 ? "+" : ""}{formatMoney(net)}
        </span>
        <span className="text-xs text-slate-400 dark:text-muted-foreground">
          {dx.netThisMonth} · {dx.inflow} {formatMoney(cur?.income ?? 0)} · {dx.outflow} {formatMoney(cur?.spent ?? 0)}
        </span>
      </div>
      <ReactECharts option={option} style={{ height: 200 }} />
    </div>
  );
}
