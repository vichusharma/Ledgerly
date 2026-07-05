"use client";

import { useHoldings } from "@/lib/api/hooks";
import { formatMoney, formatPct } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

export function HoldingsTable({ scope }: { scope: string }) {
  const { data: holdings } = useHoldings(scope);
  const { t } = useLanguage();
  const px = t("portfolio");

  const rows = holdings?.rows ?? [];

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-border dark:border-border">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{px.holdings}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border">
              {[px.instrument, px.account, px.owner, px.quantity, px.price, px.marketValue, px.gainLoss, px.weight].map(h => (
                <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: any, idx: number) => {
              const gainLoss = row.gain_loss != null ? Number(row.gain_loss) : null;
              const neg = gainLoss != null && gainLoss < 0;
              return (
                <tr key={`${row.account_id}-${row.instrument_id}-${idx}`} className="border-b border-slate-50 dark:border-border hover:bg-slate-50 dark:hover:bg-secondary">
                  <td className="px-4 py-2">
                    <p className="font-medium text-slate-800 dark:text-foreground">{row.name}</p>
                    {row.isin && <p className="text-xs text-slate-400 dark:text-muted-foreground">{row.isin}</p>}
                  </td>
                  <td className="px-4 py-2">
                    <p className="text-slate-700 dark:text-foreground">{row.account_name}</p>
                    {row.wrapper_type && <p className="text-xs text-slate-400 dark:text-muted-foreground">{row.wrapper_type}</p>}
                  </td>
                  <td className="px-4 py-2 text-slate-700 dark:text-foreground">
                    {row.owner_name}
                    {row.joint_owner_name && (
                      <span className="ml-1 text-xs px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-secondary text-slate-500 dark:text-muted-foreground">
                        +{row.joint_owner_name}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 money text-slate-700 dark:text-foreground">{row.quantity}</td>
                  <td className="px-4 py-2 money text-slate-700 dark:text-foreground">
                    {row.price != null ? formatMoney(row.price) : "—"}
                  </td>
                  <td className="px-4 py-2 money text-slate-900 dark:text-foreground font-medium">
                    {row.market_value != null ? formatMoney(row.market_value) : "—"}
                  </td>
                  <td className={`px-4 py-2 money font-medium ${gainLoss == null ? "text-slate-400 dark:text-muted-foreground" : neg ? "text-danger" : "text-success"}`}>
                    {gainLoss != null ? (
                      <>
                        {formatMoney(gainLoss)}
                        {row.gain_loss_pct != null && <span className="text-xs ml-1">({formatPct(row.gain_loss_pct)})</span>}
                      </>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-2 money text-slate-500 dark:text-muted-foreground">{formatPct(row.weight_pct)}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground text-sm">
                  {px.noData}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
