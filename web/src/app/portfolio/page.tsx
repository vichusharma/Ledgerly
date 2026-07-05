"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { KpiCard } from "@/components/finance/KpiCard";
import { AllocationChart } from "@/components/charts/AllocationChart";
import { PortfolioHero } from "@/components/portfolio/PortfolioHero";
import { AddHoldingForm } from "@/components/portfolio/AddHoldingForm";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";
import {
  usePortfolioPerformance, usePortfolioAllocation, useLots, useInstruments, useDeleteLot,
} from "@/lib/api/hooks";
import { useScope } from "@/lib/hooks/useScope";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatPct } from "@/lib/format/money";

export default function PortfolioPage() {
  const { scope } = useScope();
  const { data: perf } = usePortfolioPerformance(scope);
  const { data: alloc } = usePortfolioAllocation(scope);
  const { data: lots = [] } = useLots();
  const { data: instruments = [] } = useInstruments();
  const deleteLot = useDeleteLot();
  const [showMovements, setShowMovements] = useState(false);
  const { t } = useLanguage();
  const px = t("portfolio");

  const instrMap = new Map<unknown, { id: unknown; ticker?: string; name?: string }>(instruments.map((i: any) => [i.id, i]));

  const handleDeleteLot = async (id: number) => {
    if (confirm(px.deleteLotConfirm)) {
      await deleteLot.mutateAsync(id);
    }
  };

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{px.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{px.subtitle}</p>
        </div>

        <div className="grid grid-cols-12 gap-4 lg:gap-6">
          {/* Row 1 — hero + KPI stack */}
          <div className="col-span-12 lg:col-span-7">
            <PortfolioHero
              currentValue={perf?.current_value ?? 0}
              gainLoss={perf?.total_gain ?? 0}
              gainPct={perf?.gain_pct ?? 0}
            />
          </div>
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-4 lg:gap-6">
            <KpiCard title={px.totalInvested} value={perf ? formatMoney(perf.total_invested) : "—"} className="flex-1" />
            <KpiCard
              title={px.xirr}
              value={perf?.xirr != null ? formatPct(perf.xirr * 100) : "—"}
              subtitle={perf?.twr != null ? `TWR: ${formatPct(perf.twr * 100)}` : undefined}
              className="flex-1"
            />
          </div>

          {/* Row 2 — allocation */}
          {alloc?.by_class?.length > 0 && (
            <div className="col-span-12">
              <AllocationChart slices={alloc.by_class} variant="detailed" />
            </div>
          )}

          {/* Row 3 — add holding */}
          <AddHoldingForm />

          {/* Row 4 — holdings table */}
          <div className="col-span-12">
            <HoldingsTable scope={scope} />
          </div>

          {/* Row 5 — by wrapper */}
          {alloc?.by_wrapper?.length > 0 && (
            <div className="col-span-12">
              <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{px.byWrapper}</h3>
                <div className="space-y-2">
                  {alloc.by_wrapper.map((s: any) => (
                    <div key={s.asset_class} className="flex items-center gap-4">
                      <span className="text-sm text-slate-700 dark:text-foreground w-24 flex-shrink-0">{s.asset_class}</span>
                      <div className="flex-1 bg-slate-100 dark:bg-secondary rounded-full h-2">
                        <div className="bg-brand rounded-full h-2" style={{ width: `${Math.min(s.actual_pct, 100)}%` }} />
                      </div>
                      <span className="money text-xs text-slate-500 dark:text-muted-foreground w-20 text-right">{formatMoney(s.market_value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Row 6 — movements ledger, collapsed by default */}
          <div className="col-span-12">
            <button
              onClick={() => setShowMovements(s => !s)}
              className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-muted-foreground hover:text-slate-700 dark:hover:text-foreground mb-2"
            >
              {showMovements ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showMovements ? px.hideMovements : px.showMovements}
            </button>
            {showMovements && (
              <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-surface-border dark:border-border">
                  <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{px.movements}</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border">
                        {[px.date, px.instrument, px.type, px.quantity, px.price, px.fees, ""].map(h => (
                          <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {lots.map((lot: any) => {
                        const inst = instrMap.get(lot.instrument_id);
                        return (
                          <tr key={lot.id} className="border-b border-slate-50 dark:border-border hover:bg-slate-50 dark:hover:bg-secondary">
                            <td className="px-4 py-2 text-slate-500 dark:text-muted-foreground money">{lot.settled_at}</td>
                            <td className="px-4 py-2 font-medium text-slate-800 dark:text-foreground">
                              {inst?.ticker || inst?.name || "—"}
                            </td>
                            <td className="px-4 py-2">
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                lot.lot_type === "buy"
                                  ? "bg-success/10 text-success"
                                  : lot.lot_type === "sell"
                                  ? "bg-danger/10 text-danger"
                                  : "bg-slate-100 dark:bg-secondary text-slate-600 dark:text-muted-foreground"
                              }`}>
                                {lot.lot_type}
                              </span>
                            </td>
                            <td className="px-4 py-2 money text-slate-700 dark:text-foreground">{lot.quantity}</td>
                            <td className="px-4 py-2 money text-slate-700 dark:text-foreground">{formatMoney(lot.price, lot.currency)}</td>
                            <td className="px-4 py-2 money text-slate-400 dark:text-muted-foreground">{formatMoney(lot.fees)}</td>
                            <td className="px-4 py-2 text-right">
                              <button
                                onClick={() => handleDeleteLot(lot.id)}
                                className="text-slate-400 hover:text-danger"
                                title={px.deleteLot}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                      {lots.length === 0 && (
                        <tr>
                          <td colSpan={7} className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground text-sm">
                            {px.noMovements}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
