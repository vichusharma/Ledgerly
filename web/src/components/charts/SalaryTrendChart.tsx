"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatCompact, getLocale } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface PayslipPoint {
  pay_period: string;
  gross: number | string | null;
  net_taxable: number | string | null;
  net_paid: number | string | null;
}

function monthLabel(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(getLocale(), { month: "short", year: "2-digit" });
}

const num = (v: number | string | null) => (v == null ? 0 : Number(v));

export function SalaryTrendChart({ payslips, title }: { payslips: PayslipPoint[]; title: string }) {
  const { t } = useLanguage();
  const sx = t("salary");
  const sorted = [...payslips].sort((a, b) => a.pay_period.localeCompare(b.pay_period));

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (ps: any[]) =>
        `${ps[0].axisValue}<br/>${ps.map((p: any) => `${p.seriesName}: ${formatMoney(p.value)}`).join("<br/>")}`,
    },
    legend: {
      top: 0,
      textStyle: { color: "#94a3b8", fontSize: 11 },
    },
    grid: { left: 56, right: 12, top: 32, bottom: 24 },
    xAxis: {
      type: "category",
      data: sorted.map((p) => monthLabel(p.pay_period)),
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
      {
        name: sx.gross, type: "line", data: sorted.map((p) => num(p.gross)),
        lineStyle: { width: 2.5, color: "#6366f1" }, itemStyle: { color: "#6366f1" }, symbolSize: 6,
      },
      {
        name: sx.netTaxable, type: "line", data: sorted.map((p) => num(p.net_taxable)),
        lineStyle: { width: 2.5, color: "#94a3b8" }, itemStyle: { color: "#94a3b8" }, symbolSize: 6,
      },
      {
        name: sx.netPaid, type: "line", data: sorted.map((p) => num(p.net_paid)),
        lineStyle: { width: 2.5, color: "#10b981" }, itemStyle: { color: "#10b981" }, symbolSize: 6,
      },
    ],
  };

  return (
    <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{title}</h3>
      {sorted.length === 0 ? (
        <div className="flex items-center justify-center h-[220px]">
          <p className="text-sm text-slate-400 dark:text-muted-foreground">{sx.noData}</p>
        </div>
      ) : (
        <ReactECharts option={option} style={{ height: 220 }} />
      )}
    </div>
  );
}
