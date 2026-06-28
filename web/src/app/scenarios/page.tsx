"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ScenarioChart } from "@/components/charts/ScenarioChart";
import { useScenarios, useRunScenario, useLoans } from "@/lib/api/hooks";
import { apiClient } from "@/lib/api/client";
import { formatMoney } from "@/lib/format/money";
import { useQueryClient } from "@tanstack/react-query";

const DEFAULT_PARAMS = {
  horizon_months: 240,
  lump_sum: 20000,
  monthly: 0,
  returns: { low: 0.02, base: 0.05, high: 0.08 },
};

export default function ScenariosPage() {
  const { data: scenarios = [] } = useScenarios();
  const { data: loans = [] } = useLoans();
  const runScenario = useRunScenario();
  const qc = useQueryClient();

  const [params, setParams] = useState({
    lumpSum: DEFAULT_PARAMS.lump_sum,
    monthly: DEFAULT_PARAMS.monthly,
    horizon: DEFAULT_PARAMS.horizon_months,
    mortgageId: null as number | null,
    low: 2, base: 5, high: 8,
  });

  const [result, setResult] = useState<any>(null);
  const [activeLabel, setActiveLabel] = useState("base");
  const [scenarioName, setScenarioName] = useState("Nouveau scénario");

  const handleRun = async () => {
    // Create scenario first, then run it
    const sc = await apiClient.post("/scenarios", {
      name: scenarioName,
      type: "invest_vs_prepay",
    }).then(r => r.data);

    const res = await runScenario.mutateAsync({
      id: sc.id,
      params: {
        horizon_months: params.horizon,
        lump_sum: params.lumpSum,
        monthly: params.monthly,
        mortgage_id: params.mortgageId,
        returns: {
          low: params.low / 100,
          base: params.base / 100,
          high: params.high / 100,
        },
      },
    });
    setResult(res);
  };

  const activeResult = result?.results?.[activeLabel];

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900">Simulateur</h1>
        <p className="text-sm text-slate-500">
          Comparez « investir la somme » vs. « rembourser le crédit par anticipation »
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Parameters panel */}
          <div className="bg-white rounded-xl border border-surface-border p-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Paramètres</h3>

            <label className="block">
              <span className="text-xs text-slate-500">Nom du scénario</span>
              <input
                value={scenarioName}
                onChange={e => setScenarioName(e.target.value)}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            <label className="block">
              <span className="text-xs text-slate-500">Capital (€)</span>
              <input
                type="number"
                value={params.lumpSum}
                onChange={e => setParams(p => ({ ...p, lumpSum: Number(e.target.value) }))}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 money focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            <label className="block">
              <span className="text-xs text-slate-500">Versement mensuel (€)</span>
              <input
                type="number"
                value={params.monthly}
                onChange={e => setParams(p => ({ ...p, monthly: Number(e.target.value) }))}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 money focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            <label className="block">
              <span className="text-xs text-slate-500">Horizon (mois)</span>
              <input
                type="number"
                value={params.horizon}
                onChange={e => setParams(p => ({ ...p, horizon: Number(e.target.value) }))}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 money focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            {loans.length > 0 && (
              <label className="block">
                <span className="text-xs text-slate-500">Crédit</span>
                <select
                  value={params.mortgageId ?? ""}
                  onChange={e => setParams(p => ({ ...p, mortgageId: e.target.value ? Number(e.target.value) : null }))}
                  className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none"
                >
                  <option value="">Aucun</option>
                  {loans.map((l: any) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </label>
            )}

            <div className="border-t border-surface-border pt-3 space-y-2">
              <p className="text-xs text-slate-500">Rendements annuels (%)</p>
              {(["low", "base", "high"] as const).map(k => (
                <div key={k} className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-10 capitalize">{k === "low" ? "Bas" : k === "base" ? "Base" : "Haut"}</span>
                  <input
                    type="number"
                    step="0.5"
                    value={params[k]}
                    onChange={e => setParams(p => ({ ...p, [k]: Number(e.target.value) }))}
                    className="flex-1 text-sm border border-surface-border rounded-lg px-3 py-1.5 money focus:outline-none focus:ring-2 focus:ring-brand/20"
                  />
                  <span className="text-xs text-slate-400">%</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleRun}
              disabled={runScenario.isPending}
              className="w-full bg-brand text-white text-sm font-medium py-2.5 rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {runScenario.isPending ? "Calcul…" : "Lancer la simulation"}
            </button>
          </div>

          {/* Results */}
          <div className="lg:col-span-2 space-y-4">
            {result && (
              <>
                {/* Tab selector */}
                <div className="flex gap-2">
                  {["low", "base", "high"].map(label => (
                    <button
                      key={label}
                      onClick={() => setActiveLabel(label)}
                      className={`px-4 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        activeLabel === label
                          ? "bg-brand border-brand text-white"
                          : "border-surface-border text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      {label === "low" ? "Bas" : label === "base" ? "Base" : "Haut"} ({
                        label === "low" ? params.low : label === "base" ? params.base : params.high
                      }%)
                    </button>
                  ))}
                </div>

                {activeResult && (
                  <>
                    <ScenarioChart
                      series={activeResult.series}
                      breakeven_month={activeResult.breakeven_month}
                      label={`${activeLabel} (${
                        activeLabel === "low" ? params.low : activeLabel === "base" ? params.base : params.high
                      }%)`}
                    />

                    {/* Interpretation */}
                    <div className="bg-white rounded-xl border border-surface-border p-5 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-slate-400">Valeur finale (investir)</p>
                        <p className="money font-semibold text-slate-900">{formatMoney(activeResult.invest_net_worth_end)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Valeur finale (rembourser)</p>
                        <p className="money font-semibold text-slate-900">{formatMoney(activeResult.prepay_net_worth_end)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Écart final</p>
                        <p className={`money font-semibold ${parseFloat(activeResult.delta_end) >= 0 ? "text-success" : "text-danger"}`}>
                          {parseFloat(activeResult.delta_end) >= 0 ? "+" : ""}{formatMoney(activeResult.delta_end)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Intérêts économisés si remboursement</p>
                        <p className="money font-semibold text-slate-700">{formatMoney(activeResult.interest_saved_if_prepay)}</p>
                      </div>
                      <div className="col-span-2 border-t pt-3">
                        <p className="text-sm text-slate-600 italic">{activeResult.interpretation}</p>
                      </div>
                    </div>
                  </>
                )}
              </>
            )}

            {/* Saved scenarios */}
            {scenarios.length > 0 && (
              <div className="bg-white rounded-xl border border-surface-border p-5">
                <h3 className="text-sm font-semibold text-slate-700 mb-3">Scénarios sauvegardés</h3>
                <div className="space-y-2">
                  {scenarios.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                      <span className="text-sm text-slate-700">{s.name}</span>
                      <span className="text-xs text-slate-400">{s.last_run_at ? new Date(s.last_run_at).toLocaleDateString("fr-FR") : "Jamais exécuté"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
