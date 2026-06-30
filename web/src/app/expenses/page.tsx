"use client";

import { useState, useRef, useCallback, useMemo, Fragment } from "react";
import { AppShell } from "@/components/AppShell";
import {
  useTransactions, useTransactionAnalytics,
  useLabels, useCreateLabel, useSetTransactionLabels,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";
import { KpiCard } from "@/components/finance/KpiCard";
import { SpendingTrendChart } from "@/components/charts/SpendingTrendChart";
import { LabelDonutChart } from "@/components/charts/LabelDonutChart";
import { Tag, Plus, X, Check, ChevronDown, Store } from "lucide-react";

// ── Period helpers ────────────────────────────────────────────────────────────

type Period = "month" | "3m" | "year" | "all";

function periodRange(p: Period): { from_date?: string; to_date?: string } {
  const today = new Date();
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  const to_date = iso(today);
  if (p === "all") return {};
  if (p === "month") return { from_date: iso(new Date(today.getFullYear(), today.getMonth(), 1)), to_date };
  if (p === "year") return { from_date: iso(new Date(today.getFullYear(), 0, 1)), to_date };
  return { from_date: iso(new Date(today.getFullYear(), today.getMonth() - 2, 1)), to_date };
}

// ── Label types ───────────────────────────────────────────────────────────────

interface Label { id: number; name: string; color: string }

// 9 preset colours the user can pick from when creating a label.
const PRESET_COLORS = [
  "#ef4444", "#f97316", "#eab308",
  "#22c55e", "#06b6d4", "#3b82f6",
  "#8b5cf6", "#ec4899", "#6b7280",
];

// ── Label chip ────────────────────────────────────────────────────────────────

function LabelChip({ label, onRemove }: { label: Label; onRemove?: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: label.color }}
    >
      {label.name}
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="ml-0.5 opacity-70 hover:opacity-100"
        >
          <X size={10} />
        </button>
      )}
    </span>
  );
}

// ── Inline label editor (renders as a <tr> spanning all columns) ──────────────

function LabelEditorRow({
  tx,
  allLabels,
  colSpan,
  onClose,
}: {
  tx: any;
  allLabels: Label[];
  colSpan: number;
  onClose: () => void;
}) {
  const { t } = useLanguage();
  const dx = t("expenses");
  const setLabels = useSetTransactionLabels();
  const createLabel = useCreateLabel();

  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState(PRESET_COLORS[5]);
  const inputRef = useRef<HTMLInputElement>(null);

  const appliedIds: Set<number> = new Set((tx.labels || []).map((l: Label) => l.id));

  const toggle = (label: Label) => {
    const next = new Set(appliedIds);
    if (next.has(label.id)) next.delete(label.id); else next.add(label.id);
    setLabels.mutate({ txnId: tx.id, labelIds: [...next] });
  };

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    const newLabel: Label = await createLabel.mutateAsync({ name, color: newColor });
    // Immediately apply the new label to this transaction.
    setLabels.mutate({ txnId: tx.id, labelIds: [...appliedIds, newLabel.id] });
    setNewName("");
  };

  return (
    <tr className="bg-slate-50 dark:bg-secondary border-b border-slate-100 dark:border-border">
      <td colSpan={colSpan} className="px-4 py-3">
        <div className="flex flex-wrap items-start gap-4">
          {/* Existing labels — toggleable */}
          <div className="flex flex-wrap gap-1.5 items-center">
            {allLabels.length === 0 && (
              <span className="text-xs text-slate-400 dark:text-muted-foreground">{dx.noLabels}</span>
            )}
            {allLabels.map((lb) => {
              const applied = appliedIds.has(lb.id);
              return (
                <button
                  key={lb.id}
                  onClick={() => toggle(lb)}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border transition-opacity ${
                    applied ? "text-white opacity-100" : "opacity-50 hover:opacity-80"
                  }`}
                  style={{
                    backgroundColor: applied ? lb.color : "transparent",
                    borderColor: lb.color,
                    color: applied ? "white" : lb.color,
                  }}
                >
                  {applied && <Check size={10} />}
                  {lb.name}
                </button>
              );
            })}
          </div>

          {/* Separator */}
          <div className="w-px self-stretch bg-slate-200 dark:bg-border" />

          {/* New label creator */}
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); }}
              placeholder={dx.labelName}
              className="h-6 px-2 text-xs rounded border border-surface-border dark:border-border bg-white dark:bg-card dark:text-foreground focus:outline-none focus:ring-1 focus:ring-brand/30 w-28"
            />
            <div className="flex gap-1">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => setNewColor(c)}
                  className="w-4 h-4 rounded-full transition-transform"
                  style={{
                    backgroundColor: c,
                    outline: newColor === c ? `2px solid ${c}` : "none",
                    outlineOffset: "2px",
                  }}
                />
              ))}
            </div>
            <button
              onClick={handleCreate}
              disabled={!newName.trim() || createLabel.isPending}
              className="h-6 px-2 text-xs rounded bg-brand text-white disabled:opacity-40 flex items-center gap-1"
            >
              <Plus size={10} /> {dx.createLabel}
            </button>
          </div>

          {/* Close */}
          <button
            onClick={onClose}
            className="ml-auto text-slate-400 hover:text-slate-600 dark:text-muted-foreground dark:hover:text-foreground"
          >
            <X size={14} />
          </button>
        </div>
      </td>
    </tr>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ExpensesPage() {
  const { t } = useLanguage();
  const dx = t("expenses");

  const [period, setPeriod] = useState<Period>("3m");
  const [filter, setFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showList, setShowList] = useState(false);

  const range = useMemo(() => periodRange(period), [period]);

  const { data: analytics } = useTransactionAnalytics(range);
  const { data: txns = [], isLoading } = useTransactions({ ...range, limit: 500 });
  const { data: allLabels = [] } = useLabels();

  const filtered = txns.filter((tx: any) =>
    tx.description.toLowerCase().includes(filter.toLowerCase())
  );

  const toggleExpand = useCallback((id: number) => {
    setExpandedId(prev => prev === id ? null : id);
  }, []);

  const COL_COUNT = 4;

  // ── Derived analytics for display ──
  const totalSpent = Number(analytics?.total_spent ?? 0);
  const totalIncome = Number(analytics?.total_income ?? 0);
  const net = Number(analytics?.net ?? 0);
  const txnCount = analytics?.txn_count ?? 0;
  const byMonth = (analytics?.by_month ?? []).map((m: any) => ({
    month: m.month, spent: Number(m.spent), income: Number(m.income),
  }));
  const byLabel = (analytics?.by_label ?? []).map((l: any) => ({
    ...l,
    name: l.name === "Unlabeled" ? dx.unlabeled : l.name,
    spent: Number(l.spent),
    pct: Number(l.pct),
  }));
  const topMerchants = (analytics?.top_merchants ?? []).map((m: any) => ({
    merchant: m.merchant, spent: Number(m.spent), count: m.count,
  }));
  const topMerchant = topMerchants[0];
  const avgTxn = txnCount > 0 ? totalSpent / txnCount : 0;
  const maxMerchant = topMerchants[0]?.spent || 1;

  const PERIODS: { key: Period; label: string }[] = [
    { key: "month", label: dx.periodMonth },
    { key: "3m", label: dx.period3m },
    { key: "year", label: dx.periodYear },
    { key: "all", label: dx.periodAll },
  ];

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header + period selector */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{dx.title}</h1>
          <div className="inline-flex rounded-lg border border-surface-border dark:border-border overflow-hidden text-sm">
            {PERIODS.map((p, i) => (
              <button
                key={p.key}
                onClick={() => setPeriod(p.key)}
                className={`px-3 py-1.5 ${i > 0 ? "border-l border-surface-border dark:border-border" : ""} ${
                  period === p.key
                    ? "bg-brand/10 text-brand font-medium"
                    : "text-slate-500 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard title={dx.totalSpent} value={formatMoney(totalSpent)} subtitle={`${formatMoney(avgTxn)} ${dx.avgTxn}`} />
          <KpiCard
            title={dx.net}
            value={formatMoney(net)}
            trend={net >= 0 ? 1 : -1}
            subtitle={`${dx.income}: ${formatMoney(totalIncome)}`}
          />
          <KpiCard
            title={dx.topMerchant}
            value={topMerchant ? formatMoney(topMerchant.spent) : "—"}
            subtitle={topMerchant ? topMerchant.merchant : ""}
          />
          <KpiCard title={dx.txnCount} value={String(txnCount)} />
        </div>

        {/* Monthly trend */}
        {byMonth.length > 0 && <SpendingTrendChart data={byMonth} title={dx.byMonth} />}

        {/* Label donut + top merchants */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {byLabel.length > 0 && <LabelDonutChart data={byLabel} title={dx.byLabel} />}

          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-5">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4 flex items-center gap-1.5">
              <Store size={14} /> {dx.topMerchants}
            </h3>
            <div className="space-y-3">
              {topMerchants.map((m: any) => (
                <div key={m.merchant}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-700 dark:text-foreground truncate">{m.merchant}</span>
                    <span className="money text-slate-500 dark:text-muted-foreground whitespace-nowrap ml-2">{formatMoney(m.spent)}</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 dark:bg-secondary rounded-full">
                    <div className="h-1.5 bg-brand rounded-full" style={{ width: `${Math.round((m.spent / maxMerchant) * 100)}%` }} />
                  </div>
                </div>
              ))}
              {topMerchants.length === 0 && (
                <p className="text-sm text-slate-400 dark:text-muted-foreground">{dx.noTransactions}</p>
              )}
            </div>
          </div>
        </div>

        {/* Collapsible transaction list */}
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
          <button
            onClick={() => setShowList((s) => !s)}
            aria-expanded={showList}
            className="w-full flex items-center justify-between px-5 py-3.5 text-sm text-slate-700 dark:text-foreground hover:bg-slate-50 dark:hover:bg-secondary"
          >
            <span className="flex items-center gap-2 font-medium">
              {dx.allTransactions}
              <span className="text-slate-400 dark:text-muted-foreground font-normal">({txns.length})</span>
            </span>
            <ChevronDown size={16} className={`text-slate-400 transition-transform ${showList ? "rotate-180" : ""}`} />
          </button>

          {showList && (
            <div className="border-t border-surface-border dark:border-border">
              {/* Search */}
              <div className="p-4">
                <input
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder={dx.searchPlaceholder}
                  className="w-full pl-4 pr-4 py-2 rounded-lg border border-surface-border dark:border-border text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground dark:placeholder:text-muted-foreground"
                />
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border bg-slate-50 dark:bg-secondary">
                      {[dx.date, dx.description, dx.labels, dx.amount].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium last:text-right">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice(0, 200).map((tx: any) => {
                      const txLabels: Label[] = tx.labels || [];
                      const isExpanded = expandedId === tx.id;

                      return (
                        <Fragment key={tx.id}>
                          <tr
                            onClick={() => toggleExpand(tx.id)}
                            className={`border-b border-slate-50 dark:border-border cursor-pointer select-none transition-colors ${
                              isExpanded
                                ? "bg-slate-50 dark:bg-secondary"
                                : "hover:bg-slate-50 dark:hover:bg-secondary"
                            }`}
                          >
                            <td className="px-4 py-2.5 money text-slate-400 dark:text-muted-foreground text-xs whitespace-nowrap">
                              {formatDate(tx.date)}
                            </td>
                            <td className="px-4 py-2.5 text-slate-700 dark:text-foreground max-w-xs truncate">
                              {tx.description || "—"}
                            </td>
                            <td className="px-4 py-2.5">
                              <div className="flex flex-wrap gap-1 items-center min-h-[1.25rem]">
                                {txLabels.map((lb) => (
                                  <LabelChip key={lb.id} label={lb} />
                                ))}
                                {txLabels.length === 0 && (
                                  <span className="inline-flex items-center gap-1 text-xs text-slate-300 dark:text-muted-foreground">
                                    <Tag size={11} />
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className={`px-4 py-2.5 money text-right font-medium ${
                              parseFloat(tx.amount) < 0 ? "text-danger" : "text-success"
                            }`}>
                              {formatMoney(tx.amount)}
                            </td>
                          </tr>
                          {isExpanded && (
                            <LabelEditorRow
                              tx={tx}
                              allLabels={allLabels}
                              colSpan={COL_COUNT}
                              onClose={() => setExpandedId(null)}
                            />
                          )}
                        </Fragment>
                      );
                    })}
                    {filtered.length === 0 && !isLoading && (
                      <tr>
                        <td colSpan={COL_COUNT} className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground">
                          {dx.noTransactions}
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
    </AppShell>
  );
}
