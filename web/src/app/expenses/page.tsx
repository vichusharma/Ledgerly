"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useTransactions, useCategories } from "@/lib/api/hooks";
import { formatMoney, formatDate } from "@/lib/format/money";

export default function ExpensesPage() {
  const [filter, setFilter] = useState("");
  const { data: txns = [], isLoading } = useTransactions();
  const { data: categories = [] } = useCategories();

  const catMap = new Map(categories.map((c: any) => [c.id, c]));

  const filtered = txns.filter((t: any) =>
    t.description.toLowerCase().includes(filter.toLowerCase())
  );

  const totalExpenses = filtered
    .filter((t: any) => t.amount < 0)
    .reduce((sum: number, t: any) => sum + Math.abs(parseFloat(t.amount)), 0);

  const totalIncome = filtered
    .filter((t: any) => t.amount > 0)
    .reduce((sum: number, t: any) => sum + parseFloat(t.amount), 0);

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-900">Dépenses & Revenus</h1>
          <div className="flex gap-4 text-sm">
            <div className="text-right">
              <p className="text-slate-400 text-xs">Dépenses</p>
              <p className="font-semibold money text-danger">{formatMoney(totalExpenses)}</p>
            </div>
            <div className="text-right">
              <p className="text-slate-400 text-xs">Revenus</p>
              <p className="font-semibold money text-success">{formatMoney(totalIncome)}</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Rechercher une transaction…"
            className="w-full pl-4 pr-4 py-2.5 rounded-xl border border-surface-border text-sm focus:outline-none focus:ring-2 focus:ring-brand/20"
          />
        </div>

        {/* Transaction list */}
        <div className="bg-white rounded-xl border border-surface-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-surface-border bg-slate-50">
                  {["Date", "Description", "Catégorie", "Montant"].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium last:text-right">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((t: any) => {
                  const cat = catMap.get(t.category_id);
                  return (
                    <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-2.5 money text-slate-400 text-xs whitespace-nowrap">
                        {formatDate(t.date)}
                      </td>
                      <td className="px-4 py-2.5 text-slate-700 max-w-xs truncate">
                        {t.description || "—"}
                      </td>
                      <td className="px-4 py-2.5">
                        {cat ? (
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                            {cat.name}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-300">—</span>
                        )}
                      </td>
                      <td className={`px-4 py-2.5 money text-right font-medium ${
                        parseFloat(t.amount) < 0 ? "text-danger" : "text-success"
                      }`}>
                        {formatMoney(t.amount)}
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && !isLoading && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                      Aucune transaction — importez un CSV
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
