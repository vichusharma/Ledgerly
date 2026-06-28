"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useTransactions, useCategories } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";

export default function ExpensesPage() {
  const [filter, setFilter] = useState("");
  const { data: txns = [], isLoading } = useTransactions();
  const { data: categories = [] } = useCategories();
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
                  {[dx.date, dx.description, dx.category, dx.amount].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium last:text-right">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((tx: any) => {
                  const cat = catMap.get(tx.category_id);
                  return (
                    <tr key={tx.id} className="border-b border-slate-50 dark:border-border hover:bg-slate-50 dark:hover:bg-secondary">
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
                      <td className={`px-4 py-2.5 money text-right font-medium ${
                        parseFloat(tx.amount) < 0 ? "text-danger" : "text-success"
                      }`}>
                        {formatMoney(tx.amount)}
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && !isLoading && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400 dark:text-muted-foreground">
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
