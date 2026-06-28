"use client";

import ReactECharts from "echarts-for-react";
import { formatMoney, formatPct } from "@/lib/format/money";

interface Slice {
  asset_class: string;
  market_value: number;
  actual_pct: number;
  target_pct: number;
  drift_pct: number;
}

const COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

export function AllocationChart({ slices }: { slices: Slice[] }) {
  const pieOption = {
    tooltip: {
      formatter: (p: any) =>
        `${p.name}<br/>${formatMoney(p.data.value)}<br/>${formatPct(p.percent)}`,
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        data: slices.map((s, i) => ({
          name: s.asset_class,
          value: s.market_value,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
        label: { formatter: "{b}\n{d}%", fontSize: 11 },
      },
    ],
  };

  return (
    <div className="bg-white rounded-xl border border-surface-border p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">Allocation des actifs</h3>
      <div className="flex gap-6">
        <ReactECharts option={pieOption} style={{ height: 220, width: 220 }} />
        <div className="flex-1 space-y-2 mt-2">
          <div className="grid grid-cols-4 text-xs text-slate-400 font-medium mb-1">
            <span>Classe</span>
            <span className="text-right">Actuel</span>
            <span className="text-right">Cible</span>
            <span className="text-right">Écart</span>
          </div>
          {slices.map((s, i) => (
            <div key={s.asset_class} className="grid grid-cols-4 text-xs items-center">
              <div className="flex items-center gap-1.5">
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: COLORS[i % COLORS.length] }}
                />
                <span className="text-slate-700 truncate">{s.asset_class}</span>
              </div>
              <span className="text-right money text-slate-600">{formatPct(s.actual_pct)}</span>
              <span className="text-right money text-slate-400">{formatPct(s.target_pct)}</span>
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
      </div>
    </div>
  );
}
