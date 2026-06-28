"use client";

import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { NetWorthChart } from "@/components/charts/NetWorthChart";
import { AllocationChart } from "@/components/charts/AllocationChart";
import { useNetWorth, useNetWorthSeries, usePortfolioPerformance, usePortfolioAllocation } from "@/lib/api/hooks";
import { useScope } from "@/lib/hooks/useScope";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatPct } from "@/lib/format/money";

export default function DashboardPage() {
  const { scope } = useScope();
  const { data: nw, isLoading: nwLoading } = useNetWorth(scope);
  const { data: series = [] } = useNetWorthSeries(scope);
  const { data: perf } = usePortfolioPerformance(scope);
  const { data: alloc } = usePortfolioAllocation(scope);
  const { t } = useLanguage();
  const dx = t("dashboard");

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{dx.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{dx.subtitle}</p>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title={dx.netWorth}
            value={nw ? formatMoney(nw.current) : "—"}
            subtitle={nw ? `${dx.assets}: ${formatMoney(nw.assets)}` : undefined}
            className="col-span-2 lg:col-span-1"
          />
          <KpiCard
            title={dx.totalAssets}
            value={nw ? formatMoney(nw.assets) : "—"}
          />
          <KpiCard
            title={dx.totalLiabilities}
            value={nw ? formatMoney(nw.liabilities) : "—"}
            trend={-1}
          />
          <KpiCard
            title={dx.performance}
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
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{dx.byPerson}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(nw.by_person).map(([name, breakdown]: [string, any]) => (
                <div key={name} className="p-3 bg-slate-50 dark:bg-secondary rounded-lg">
                  <p className="text-sm font-medium text-slate-700 dark:text-foreground">{name}</p>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500 dark:text-muted-foreground">{dx.assets}</span>
                      <span className="money text-slate-700 dark:text-foreground">{formatMoney(breakdown.assets)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500 dark:text-muted-foreground">{dx.liabilities}</span>
                      <span className="money text-danger">{formatMoney(breakdown.liabilities)}</span>
                    </div>
                    <div className="flex justify-between text-xs font-semibold border-t dark:border-border pt-1 mt-1">
                      <span className="text-slate-700 dark:text-foreground">{dx.net}</span>
                      <span className="money text-slate-900 dark:text-foreground">{formatMoney(breakdown.net_worth)}</span>
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
