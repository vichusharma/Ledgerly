"use client";

import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { NetWorthHero } from "@/components/finance/NetWorthHero";
import { RecentActivity } from "@/components/finance/RecentActivity";
import { NetWorthChart } from "@/components/charts/NetWorthChart";
import { CashflowChart } from "@/components/charts/CashflowChart";
import { AllocationChart } from "@/components/charts/AllocationChart";
import {
  useNetWorth, useNetWorthSeries, usePortfolioPerformance,
  usePortfolioAllocation, useTransactionAnalytics, useTaxEstimate,
  useFilingSnapshot,
} from "@/lib/api/hooks";
import { useScope } from "@/lib/hooks/useScope";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatPct } from "@/lib/format/money";

export default function DashboardPage() {
  const { scope } = useScope();
  const { data: nw } = useNetWorth(scope);
  const { data: series = [] } = useNetWorthSeries(scope);
  const { data: perf } = usePortfolioPerformance(scope);
  const { data: alloc } = usePortfolioAllocation(scope);
  const { data: analytics } = useTransactionAnalytics();
  const { data: taxEstimate } = useTaxEstimate(new Date().getFullYear());
  const { data: filingSnapshot } = useFilingSnapshot(new Date().getFullYear());
  const { t } = useLanguage();
  const dx = t("dashboard");
  const px = t("portfolio");
  const tx = t("tax");

  const taxBalance = taxEstimate ? Number(taxEstimate.balance) : 0;
  const taxOwes = taxBalance > 0;
  const filingBalance = filingSnapshot ? Number(filingSnapshot.payload.balance) : 0;
  const filingOwes = filingBalance > 0;

  const byMonth = (analytics?.by_month ?? []).map((m: any) => ({
    month: m.month, spent: Number(m.spent), income: Number(m.income),
  }));

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{dx.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{dx.subtitle}</p>
        </div>

        <div className="grid grid-cols-12 gap-4 lg:gap-6">
          {/* Row 1 — hero + secondary KPIs */}
          <div className="col-span-12 lg:col-span-7">
            <NetWorthHero current={nw?.current ?? 0} series={series} />
          </div>
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-4 lg:gap-6">
            <KpiCard title={dx.totalAssets} value={nw ? formatMoney(nw.assets) : "—"} className="flex-1" />
            <KpiCard title={dx.totalLiabilities} value={nw ? formatMoney(nw.liabilities) : "—"} className="flex-1" />
            <KpiCard
              title={dx.performance}
              value={perf?.xirr != null ? formatPct(perf.xirr * 100) : "—"}
              subtitle={perf?.twr != null ? `TWR ${formatPct(perf.twr * 100)}` : undefined}
              trend={perf?.xirr ?? 0}
              className="flex-1"
            />
            {taxEstimate && (
              <Link href="/tax" className="flex-1 block hover:opacity-90 transition-opacity">
                <KpiCard
                  title={dx.taxEstimateTitle}
                  value={formatMoney(Math.abs(taxBalance))}
                  subtitle={taxOwes ? tx.balanceOwe : tx.balanceRefund}
                  trend={taxOwes ? -1 : 1}
                  className="h-full"
                />
              </Link>
            )}
            {filingSnapshot && (
              <Link href="/tax-filing" className="flex-1 block hover:opacity-90 transition-opacity">
                <KpiCard
                  title={dx.taxFilingTitle}
                  value={formatMoney(Math.abs(filingBalance))}
                  subtitle={filingOwes ? tx.balanceOwe : tx.balanceRefund}
                  trend={filingOwes ? -1 : 1}
                  className="h-full"
                />
              </Link>
            )}
          </div>

          {/* Row 2 — net worth evolution */}
          {series.length > 0 && (
            <div className="col-span-12">
              <NetWorthChart data={series} />
            </div>
          )}

          {/* Row 3 — cashflow + allocation */}
          {byMonth.length > 0 && (
            <div className="col-span-12 lg:col-span-7">
              <CashflowChart data={byMonth} title={dx.cashflowTitle} />
            </div>
          )}
          {alloc?.by_class?.length > 0 && (
            <div className="col-span-12 lg:col-span-5">
              <AllocationChart slices={alloc.by_class} title={px.allocationTitle} variant="compact" />
            </div>
          )}

          {/* Row 4 — by person + recent activity */}
          {nw?.by_person && Object.keys(nw.by_person).length > 0 && (
            <div className="col-span-12 lg:col-span-7">
              <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
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
            </div>
          )}
          <div className="col-span-12 lg:col-span-5">
            <RecentActivity title={dx.recentActivity} />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
