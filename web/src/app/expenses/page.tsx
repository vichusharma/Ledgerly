"use client";

import { useState, useRef, useCallback } from "react";
import { AppShell } from "@/components/AppShell";
import {
  useTransactions, useCategories,
  useLabels, useCreateLabel, useSetTransactionLabels,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";
import { Tag, Plus, X, Check } from "lucide-react";

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
  const [filter, setFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: txns = [], isLoading } = useTransactions();
  const { data: categories = [] } = useCategories();
  const { data: allLabels = [] } = useLabels();
  const { t } = useLanguage();
  const dx = t("expenses");

  const catMap = new Map<unknown, { id: unknown; name: string }>(categories.map((c: any) => [c.id, c]));

  const filtered = txns.filter((tx: any) =>
    tx.description.toLowerCase().includes(filter.toLowerCase())
  );

  const totalExpenses = filtered
    .filter((tx: any) => tx.amount < 0)
    .reduce((sum: number, tx: any) => sum + Math.abs(parseFloat(tx.amount)), 0);

  const totalIncome = filtered
    .filter((tx: any) => tx.amount > 0)
    .reduce((sum: number, tx: any) => sum + parseFloat(tx.amount), 0);

  const toggleExpand = useCallback((id: number) => {
    setExpandedId(prev => prev === id ? null : id);
  }, []);

  const COL_COUNT = 5;

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">
            {dx.title} &amp; {dx.income}
          </h1>
          <div className="flex gap-4 text-sm">
            <div className="text-right">
              <p className="text-slate-400 dark:text-muted-foreground text-xs">{dx.title}</p>
              <p className="font-semibold money text-danger">{formatMoney(totalExpenses)}</p>
            </div>
            <div className="text-right">
              <p className="text-slate-400 dark:text-muted-foreground text-xs">{dx.income}</p>
              <p className="font-semibold money text-success">{formatMoney(totalIncome)}</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder={dx.searchPlaceholder}
            className="w-full pl-4 pr-4 py-2.5 rounded-xl border border-surface-border dark:border-border text-sm focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground dark:placeholder:text-muted-foreground"
          />
        </div>

        {/* Transaction list */}
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-400 dark:text-muted-foreground border-b border-surface-border dark:border-border bg-slate-50 dark:bg-secondary">
                  {[dx.date, dx.description, dx.category, dx.labels, dx.amount].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium last:text-right">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((tx: any) => {
                  const cat = catMap.get(tx.category_id);
                  const txLabels: Label[] = tx.labels || [];
                  const isExpanded = expandedId === tx.id;

                  return (
                    <>
                      <tr
                        key={tx.id}
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
                          {cat ? (
                            <span className="text-xs bg-slate-100 dark:bg-secondary text-slate-600 dark:text-muted-foreground px-2 py-0.5 rounded-full">
                              {cat.name}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-300 dark:text-muted-foreground">—</span>
                          )}
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
                    </>
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
      </div>
    </AppShell>
  );
}
