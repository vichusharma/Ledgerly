"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatPct } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface Slice {
  asset_class: string;
  market_value: number;
  actual_pct: number;
  target_pct: number;
  drift_pct: number;
}

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

export function AllocationChart({
  slices,
  title,
  variant = "detailed",
}: {
  slices: Slice[];
  title?: string;
  variant?: "detailed" | "compact";
}) {
  const { t } = useLanguage();
  const px = t("portfolio");
  const heading = title ?? px.allocationTitle;
  const compact = variant === "compact";

  const pieOption = {
    tooltip: {
      formatter: (p: any) =>
        `${p.name}<br/>${formatMoney(p.data.value)}<br/>${formatPct(p.percent)}`,
    },
    series: [
      {
        type: "pie",
        radius: compact ? ["55%", "75%"] : ["40%", "70%"],
        avoidLabelOverlap: false,
        data: slices.map((s, i) => ({
          name: s.asset_class,
          value: s.market_value,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
        label: compact ? { show: false } : { formatter: "{b}\n{d}%", fontSize: 11 },
      },
    ],
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{heading}</h3>
      <div className={compact ? "flex items-center gap-4" : "flex gap-6"}>
        <ReactECharts
          option={pieOption}
          style={compact ? { height: 150, width: 150, flexShrink: 0 } : { height: 220, width: 220 }}
        />
        {compact ? (
          <div className="flex-1 space-y-2 min-w-0">
            {slices.map((s, i) => (
              <div key={s.asset_class} className="flex items-center gap-2 text-xs">
                <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="text-slate-700 dark:text-foreground truncate flex-1">{s.asset_class}</span>
                <span className="money text-slate-400 dark:text-muted-foreground">{formatPct(s.actual_pct)}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex-1 space-y-2 mt-2">
            <div className="grid grid-cols-4 text-xs text-slate-400 dark:text-muted-foreground font-medium mb-1">
              <span>{px.assetClass}</span>
              <span className="text-right">{px.current}</span>
              <span className="text-right">{px.targetPct}</span>
              <span className="text-right">{px.drift}</span>
            </div>
            {slices.map((s, i) => (
              <div key={s.asset_class} className="grid grid-cols-4 text-xs items-center">
                <div className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: COLORS[i % COLORS.length] }}
                  />
                  <span className="text-slate-700 dark:text-foreground truncate">{s.asset_class}</span>
                </div>
                <span className="text-right money text-slate-600 dark:text-muted-foreground">{formatPct(s.actual_pct)}</span>
                <span className="text-right money text-slate-400 dark:text-muted-foreground">{formatPct(s.target_pct)}</span>
                <span
                  className={`text-right money font-medium ${
                    s.drift_pct > 0 ? "text-warning" : s.drift_pct < 0 ? "text-danger" : "text-success"
                  }`}
                >
                  {s.drift_pct > 0 ? "+" : ""}{formatPct(s.drift_pct)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
