"use client";

import { useState, useCallback } from "react";
import ReactECharts from "echarts-for-react";
import { AppShell } from "@/components/AppShell";
import { apiClient } from "@/lib/api/client";
import { formatMoney, formatPct } from "@/lib/format/money";

interface MonteCarloResult {
  p10: number[];
  p50: number[];
  p90: number[];
}

interface FormState {
  current_value: string;
  monthly_contribution: string;
  annual_return_mu: string;
  annual_return_sigma: string;
  target_amount: string;
  years_horizon: string;
}

const PRESETS = [
  { label: "Conservateur", mu: "0.04", sigma: "0.08" },
  { label: "Modéré", mu: "0.07", sigma: "0.12" },
  { label: "Dynamique", mu: "0.09", sigma: "0.18" },
];

export default function MonteCarloPage() {
  const [form, setForm] = useState<FormState>({
    current_value: "50000",
    monthly_contribution: "500",
    annual_return_mu: "0.07",
    annual_return_sigma: "0.12",
    target_amount: "200000",
    years_horizon: "20",
  });
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const applyPreset = (p: typeof PRESETS[0]) => {
    setForm(f => ({ ...f, annual_return_mu: p.mu, annual_return_sigma: p.sigma }));
  };

  const run = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await apiClient.post<MonteCarloResult>("/scenarios/monte-carlo", {
        current_value: parseFloat(form.current_value),
        monthly_contribution: parseFloat(form.monthly_contribution),
        annual_return_mu: parseFloat(form.annual_return_mu),
        annual_return_sigma: parseFloat(form.annual_return_sigma),
        target_amount: parseFloat(form.target_amount),
        months_horizon: parseInt(form.years_horizon) * 12,
        n_paths: 1000,
      });
      setResult(data);
    } catch {
      setError("Erreur lors du calcul. Vérifiez les paramètres.");
    } finally {
      setLoading(false);
    }
  }, [form]);

  const months = result ? result.p50.length : 0;
  const target = parseFloat(form.target_amount);

  // Compute success probability at final month
  const successRate = result
    ? (result.p50[months - 1] >= target ? "> 50 %" : "< 50 %")
    : null;
  const finalP10 = result ? result.p10[months - 1] : null;
  const finalP50 = result ? result.p50[months - 1] : null;
  const finalP90 = result ? result.p90[months - 1] : null;

  const chartOptions = result
    ? {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          formatter: (params: any[]) =>
            `Mois ${params[0].dataIndex + 1}<br/>` +
            params.map((p: any) => `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}`).join("<br/>"),
        },
        legend: {
          data: ["P90 (optimiste)", "P50 (médian)", "P10 (pessimiste)"],
          bottom: 0,
          textStyle: { color: "#64748b", fontSize: 12 },
        },
        grid: { top: 20, right: 20, bottom: 48, left: 80 },
        xAxis: {
          type: "category",
          data: Array.from({ length: months }, (_, i) => i + 1),
          axisLabel: {
            formatter: (v: number) => v % 12 === 0 ? `A${v / 12}` : "",
            color: "#94a3b8",
            fontSize: 11,
          },
          axisLine: { lineStyle: { color: "#e2e8f0" } },
        },
        yAxis: {
          type: "value",
          axisLabel: {
            formatter: (v: number) => `${(v / 1000).toFixed(0)}k€`,
            color: "#94a3b8",
            fontSize: 11,
          },
          splitLine: { lineStyle: { color: "#f1f5f9" } },
        },
        series: [
          {
            name: "P90 (optimiste)",
            type: "line",
            data: result.p90,
            smooth: true,
            lineStyle: { color: "#22c55e", width: 1.5, type: "dashed" },
            itemStyle: { color: "#22c55e" },
            symbol: "none",
            areaStyle: { color: "rgba(34,197,94,0.06)" },
          },
          {
            name: "P50 (médian)",
            type: "line",
            data: result.p50,
            smooth: true,
            lineStyle: { color: "#3b82f6", width: 2 },
            itemStyle: { color: "#3b82f6" },
            symbol: "none",
            areaStyle: { color: "rgba(59,130,246,0.08)" },
          },
          {
            name: "P10 (pessimiste)",
            type: "line",
            data: result.p10,
            smooth: true,
            lineStyle: { color: "#ef4444", width: 1.5, type: "dashed" },
            itemStyle: { color: "#ef4444" },
            symbol: "none",
          },
          // Target line
          {
            name: "Objectif",
            type: "line",
            data: Array(months).fill(target),
            lineStyle: { color: "#f59e0b", width: 1.5, type: "dotted" },
            itemStyle: { color: "#f59e0b" },
            symbol: "none",
            tooltip: { show: false },
          },
        ],
      }
    : null;

  return (
    <AppShell>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Monte Carlo</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            1 000 chemins stochastiques · distribution p10/p50/p90
          </p>
        </div>

        {/* Parameter panel */}
        <div className="bg-white rounded-xl border border-surface-border p-5 space-y-5">
          <h2 className="text-sm font-semibold text-slate-700">Paramètres</h2>

          {/* Presets */}
          <div className="flex gap-2">
            {PRESETS.map(p => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                  form.annual_return_mu === p.mu && form.annual_return_sigma === p.sigma
                    ? "bg-brand text-white border-brand"
                    : "border-surface-border text-slate-600 hover:border-brand/40"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Valeur actuelle (€)", key: "current_value" as const, placeholder: "50000" },
              { label: "Versement mensuel (€)", key: "monthly_contribution" as const, placeholder: "500" },
              { label: "Rendement moyen (μ)", key: "annual_return_mu" as const, placeholder: "0.07" },
              { label: "Volatilité (σ)", key: "annual_return_sigma" as const, placeholder: "0.12" },
              { label: "Objectif (€)", key: "target_amount" as const, placeholder: "200000" },
              { label: "Horizon (années)", key: "years_horizon" as const, placeholder: "20" },
            ].map(({ label, key, placeholder }) => (
              <div key={key}>
                <label className="text-xs font-medium text-slate-500">{label}</label>
                <input
                  type="number"
                  step="any"
                  value={form[key]}
                  onChange={set(key)}
                  placeholder={placeholder}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 money"
                />
              </div>
            ))}
          </div>

          {error && <p className="text-xs text-danger">{error}</p>}

          <button
            onClick={run}
            disabled={loading}
            className="w-full bg-brand text-white font-medium py-2.5 rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors text-sm"
          >
            {loading ? "Calcul en cours…" : "Lancer la simulation"}
          </button>
        </div>

        {/* Results */}
        {result && (
          <>
            {/* KPI strip */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Valeur finale P10", value: finalP10! },
                { label: "Valeur finale P50 (médian)", value: finalP50! },
                { label: "Valeur finale P90", value: finalP90! },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white rounded-xl border border-surface-border p-4">
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className={`text-lg font-semibold mt-1 money ${value >= target ? "text-success" : "text-danger"}`}>
                    {formatMoney(value)}
                  </p>
                  {value < target && (
                    <p className="text-xs text-danger mt-0.5">
                      Écart: {formatMoney(target - value)}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Chart */}
            <div className="bg-white rounded-xl border border-surface-border p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-700">Distribution des trajectoires</h2>
                <span className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full font-medium">
                  Objectif: {formatMoney(target)}
                </span>
              </div>
              <ReactECharts option={chartOptions!} style={{ height: 380 }} />
            </div>

            {/* Interpretation */}
            <div className="bg-white rounded-xl border border-surface-border p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-3">Interprétation</h2>
              <div className="space-y-2 text-sm text-slate-600">
                <p>
                  Dans le <strong>scénario médian (P50)</strong>, votre portefeuille atteint{" "}
                  <span className="money font-medium">{formatMoney(finalP50!)}</span> après{" "}
                  {form.years_horizon} ans — {finalP50! >= target ? "✓ objectif atteint" : "✗ objectif non atteint"}.
                </p>
                <p>
                  Dans le <strong>scénario pessimiste (P10)</strong> — les 10 % de cas les plus défavorables —
                  la valeur finale est{" "}
                  <span className="money font-medium">{formatMoney(finalP10!)}</span>.
                </p>
                <p>
                  Dans le <strong>scénario optimiste (P90)</strong>, votre portefeuille atteint{" "}
                  <span className="money font-medium">{formatMoney(finalP90!)}</span>.
                </p>
                <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-50">
                  Hypothèses: rendement annuel μ = {formatPct(parseFloat(form.annual_return_mu))},
                  volatilité σ = {formatPct(parseFloat(form.annual_return_sigma))}.
                  Les simulations ne garantissent pas les rendements futurs.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
