"use client";

import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { AllocationChart } from "@/components/charts/AllocationChart";
import { usePortfolioPerformance, usePortfolioAllocation, useLots, useInstruments } from "@/lib/api/hooks";
import { useScope } from "@/lib/hooks/useScope";
import { formatMoney, formatPct } from "@/lib/format/money";

export default function PortfolioPage() {
  const { scope } = useScope();
  const { data: perf } = usePortfolioPerformance(scope);
  const { data: alloc } = usePortfolioAllocation(scope);
  const { data: lots = [] } = useLots();
  const { data: instruments = [] } = useInstruments();

  const instrMap = new Map<unknown, { id: unknown; ticker?: string; name?: string }>(instruments.map((i: any) => [i.id, i]));

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900">Portefeuille</h1>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard title="Valeur actuelle" value={perf ? formatMoney(perf.current_value) : "—"} />
          <KpiCard title="Total investi" value={perf ? formatMoney(perf.total_invested) : "—"} />
          <KpiCard
            title="Plus-value"
            value={perf ? formatMoney(perf.total_gain) : "—"}
            trend={perf?.gain_pct ?? 0}
            subtitle={perf ? formatPct(perf.gain_pct) : undefined}
          />
          <KpiCard
            title="XIRR"
            value={perf?.xirr != null ? formatPct(perf.xirr * 100) : "—"}
            subtitle={perf?.twr != null ? `TWR: ${formatPct(perf.twr * 100)}` : undefined}
          />
        </div>

        {alloc?.by_class && <AllocationChart slices={alloc.by_class} />}

        {/* Holdings table */}
        <div className="bg-white rounded-xl border border-surface-border overflow-hidden">
          <div className="px-5 py-4 border-b border-surface-border">
            <h3 className="text-sm font-semibold text-slate-700">Mouvements</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-surface-border">
                  {["Date", "Instrument", "Type", "Quantité", "Prix", "Frais"].map(h => (
                    <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lots.map((lot: any) => {
                  const inst = instrMap.get(lot.instrument_id);
                  return (
                    <tr key={lot.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-2 text-slate-500 money">{lot.settled_at}</td>
                      <td className="px-4 py-2 font-medium text-slate-800">
                        {inst?.ticker || inst?.name || "—"}
                      </td>
                      <td className="px-4 py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          lot.lot_type === "buy" ? "bg-green-100 text-green-700" :
                          lot.lot_type === "sell" ? "bg-red-100 text-red-700" :
                          "bg-slate-100 text-slate-600"
                        }`}>
                          {lot.lot_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 money text-slate-700">{lot.quantity}</td>
                      <td className="px-4 py-2 money text-slate-700">{formatMoney(lot.price, lot.currency)}</td>
                      <td className="px-4 py-2 money text-slate-400">{formatMoney(lot.fees)}</td>
                    </tr>
                  );
                })}
                {lots.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400 text-sm">
                      Aucun mouvement — ajoutez des lots via les comptes
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* By wrapper */}
        {alloc?.by_wrapper?.length > 0 && (
          <div className="bg-white rounded-xl border border-surface-border p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-4">Par enveloppe</h3>
            <div className="space-y-2">
              {alloc.by_wrapper.map((s: any) => (
                <div key={s.asset_class} className="flex items-center gap-4">
                  <span className="text-sm text-slate-700 w-24 flex-shrink-0">{s.asset_class}</span>
                  <div className="flex-1 bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-brand rounded-full h-2"
                      style={{ width: `${Math.min(s.actual_pct, 100)}%` }}
                    />
                  </div>
                  <span className="money text-xs text-slate-500 w-20 text-right">
                    {formatMoney(s.market_value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
