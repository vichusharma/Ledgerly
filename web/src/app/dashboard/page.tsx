"use client";

import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { NetWorthChart } from "@/components/charts/NetWorthChart";
import { AllocationChart } from "@/components/charts/AllocationChart";
import { useNetWorth, useNetWorthSeries, usePortfolioPerformance, usePortfolioAllocation } from "@/lib/api/hooks";
import { useScope } from "@/lib/hooks/useScope";
import { formatMoney, formatPct } from "@/lib/format/money";

export default function DashboardPage() {
  const { scope } = useScope();
  const { data: nw, isLoading: nwLoading } = useNetWorth(scope);
  const { data: series = [] } = useNetWorthSeries(scope);
  const { data: perf } = usePortfolioPerformance(scope);
  const { data: alloc } = usePortfolioAllocation(scope);

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Tableau de bord</h1>
          <p className="text-sm text-slate-500 mt-0.5">Vue d'ensemble du patrimoine</p>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Patrimoine net"
            value={nw ? formatMoney(nw.current) : "—"}
            subtitle={nw ? `Actifs: ${formatMoney(nw.assets)}` : undefined}
            className="col-span-2 lg:col-span-1"
          />
          <KpiCard
            title="Actifs totaux"
            value={nw ? formatMoney(nw.assets) : "—"}
          />
          <KpiCard
            title="Dettes totales"
            value={nw ? formatMoney(nw.liabilities) : "—"}
            trend={-1}
          />
          <KpiCard
            title="Performance (XIRR)"
            value={perf?.xirr != null ? formatPct(perf.xirr * 100) : "—"}
            subtitle={perf?.twr != null ? `TWR: ${formatPct(perf.twr * 100)}` : undefined}
            trend={perf?.xirr ?? 0}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {series.length > 0 && <NetWorthChart data={series} />}
          {alloc?.by_class?.length > 0 && <AllocationChart slices={alloc.by_class} />}
        </div>

        {/* Per-person breakdown */}
        {nw?.by_person && Object.keys(nw.by_person).length > 0 && (
          <div className="bg-white rounded-xl border border-surface-border p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-4">Par personne</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(nw.by_person).map(([name, breakdown]: [string, any]) => (
                <div key={name} className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-700">{name}</p>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Actifs</span>
                      <span className="money text-slate-700">{formatMoney(breakdown.assets)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Dettes</span>
                      <span className="money text-danger">{formatMoney(breakdown.liabilities)}</span>
                    </div>
                    <div className="flex justify-between text-xs font-semibold border-t pt-1 mt-1">
                      <span className="text-slate-700">Net</span>
                      <span className="money text-slate-900">{formatMoney(breakdown.net_worth)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
