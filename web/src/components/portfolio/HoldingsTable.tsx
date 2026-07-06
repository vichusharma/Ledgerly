"use client";

import { useMemo, useState } from "react";
import { Check, ChevronDown, Pencil, X } from "lucide-react";
import { useHoldings, usePriceLookupSetting, useUpdateHoldingQuantity } from "@/lib/api/hooks";
import { formatMoney, formatPct } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface OwnerGroup {
  owner: string;
  rows: any[];
  totalValue: number;
  totalGainLoss: number | null;
}

export function HoldingsTable({ scope }: { scope: string }) {
  const { data: holdings } = useHoldings(scope);
  const { data: priceLookup } = usePriceLookupSetting();
  const lookupEnabled = priceLookup?.price_lookup_enabled ?? false;
  const updateQuantity = useUpdateHoldingQuantity();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const { t } = useLanguage();
  const px = t("portfolio");
  const ax = t("accounts");

  const rows = holdings?.rows ?? [];

  const groups = useMemo<OwnerGroup[]>(() => {
    const buckets = new Map<string, any[]>();
    rows.forEach((row: any) => {
      const key = row.joint_owner_name ? `${row.owner_name} & ${row.joint_owner_name}` : row.owner_name;
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key)!.push(row);
    });
    return Array.from(buckets.entries())
      .map(([owner, groupRows]) => {
        const totalValue = groupRows.reduce(
          (s, r) => s + (r.market_value != null ? Number(r.market_value) : 0), 0
        );
        const gainLossRows = groupRows.filter(r => r.gain_loss != null);
        const totalGainLoss = gainLossRows.length
          ? gainLossRows.reduce((s, r) => s + Number(r.gain_loss), 0)
          : null;
        return { owner, rows: groupRows, totalValue, totalGainLoss };
      })
      .sort((a, b) => b.totalValue - a.totalValue);
  }, [rows]);

  const toggleGroup = (owner: string) => {
    setCollapsed(c => ({ ...c, [owner]: !c[owner] }));
  };

  const startEdit = (key: string, quantity: number) => {
    setEditingKey(key);
    setEditValue(String(quantity));
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditValue("");
  };

  const saveEdit = async (accountId: number, instrumentId: number) => {
    const quantity = Number(editValue);
    if (!Number.isFinite(quantity) || quantity < 0) return;
    try {
      await updateQuantity.mutateAsync({ account_id: accountId, instrument_id: instrumentId, quantity });
      cancelEdit();
    } catch {
      // Keep the row in edit mode so the user can see the value and retry.
    }
  };

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-border dark:border-border">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{px.holdings}</h3>
      </div>

      {groups.length === 0 && (
        <div className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground text-sm">
          {px.noData}
        </div>
      )}

      <div className="divide-y divide-surface-border dark:divide-border">
        {groups.map(group => {
          const isCollapsed = collapsed[group.owner] === true;
          const groupNeg = group.totalGainLoss != null && group.totalGainLoss < 0;
          return (
            <div key={group.owner}>
              <button
                onClick={() => toggleGroup(group.owner)}
                aria-expanded={!isCollapsed}
                className="w-full flex items-center justify-between px-5 py-3 text-sm hover:bg-slate-50 dark:hover:bg-secondary"
              >
                <span className="flex items-center gap-2 font-medium text-slate-700 dark:text-foreground">
                  {group.owner}
                  <span className="text-slate-400 dark:text-muted-foreground font-normal">({group.rows.length})</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className="money font-medium text-slate-900 dark:text-foreground">{formatMoney(group.totalValue)}</span>
                  {group.totalGainLoss != null && (
                    <span className={`money text-xs ${groupNeg ? "text-danger" : "text-success"}`}>
                      {formatMoney(group.totalGainLoss)}
                    </span>
                  )}
                  <ChevronDown
                    size={16}
                    className={`text-slate-400 transition-transform ${isCollapsed ? "" : "rotate-180"}`}
                  />
                </span>
              </button>

              {!isCollapsed && (
                <div className="overflow-x-auto border-t border-surface-border dark:border-border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border">
                        {[px.instrument, px.isin, px.account, px.quantity, px.price, px.marketValue, px.gainLoss].map(h => (
                          <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {group.rows.map((row: any, idx: number) => {
                        const gainLoss = row.gain_loss != null ? Number(row.gain_loss) : null;
                        const neg = gainLoss != null && gainLoss < 0;
                        const key = `${row.account_id}-${row.instrument_id}-${idx}`;
                        const editable = row.source === "buy" && lookupEnabled;
                        const isEditing = editingKey === key;
                        return (
                          <tr key={key} className="border-b border-slate-50 dark:border-border hover:bg-slate-50 dark:hover:bg-secondary">
                            <td className="px-4 py-2">
                              <p className="font-medium text-slate-800 dark:text-foreground">{row.name}</p>
                            </td>
                            <td className="px-4 py-2 text-xs text-slate-400 dark:text-muted-foreground">{row.isin ?? "—"}</td>
                            <td className="px-4 py-2">
                              <p className="text-slate-700 dark:text-foreground">{row.account_name}</p>
                              {row.wrapper_type && <p className="text-xs text-slate-400 dark:text-muted-foreground">{row.wrapper_type}</p>}
                            </td>
                            <td className="px-4 py-2 money text-slate-700 dark:text-foreground">
                              {isEditing ? (
                                <div className="flex items-center gap-1">
                                  <input
                                    type="number" min={0} step="any" autoFocus
                                    value={editValue}
                                    onChange={e => setEditValue(e.target.value)}
                                    className="w-20 text-sm border border-surface-border dark:border-border rounded px-1.5 py-0.5 bg-white dark:bg-secondary dark:text-foreground money"
                                  />
                                  <button
                                    onClick={() => saveEdit(row.account_id, row.instrument_id)}
                                    disabled={updateQuantity.isPending}
                                    title={ax.save}
                                    className="text-success hover:opacity-70 disabled:opacity-40"
                                  >
                                    <Check size={14} />
                                  </button>
                                  <button onClick={cancelEdit} title={ax.cancel} className="text-slate-400 hover:opacity-70">
                                    <X size={14} />
                                  </button>
                                </div>
                              ) : (
                                <div className="flex items-center gap-1.5 group">
                                  {row.quantity}
                                  {editable && (
                                    <button
                                      onClick={() => startEdit(key, row.quantity)}
                                      title={ax.edit}
                                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-600 dark:hover:text-foreground transition-opacity"
                                    >
                                      <Pencil size={12} />
                                    </button>
                                  )}
                                </div>
                              )}
                            </td>
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
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
