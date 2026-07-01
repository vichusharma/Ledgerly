"use client";

import { useTransactions } from "@/lib/api/hooks";
import { formatMoney, formatDate } from "@/lib/format/money";
import { useLanguage } from "@/lib/context/LanguageContext";

interface Label { id: number; name: string; color: string }

export function RecentActivity({ title }: { title: string }) {
  const { data: txns = [] } = useTransactions({ limit: 6 });
  const { t } = useLanguage();
  const ex = t("expenses");

  return (
    <div className="h-full bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-4">{title}</h3>
      <div className="space-y-2.5">
        {txns.slice(0, 6).map((tx: any) => {
          const neg = parseFloat(tx.amount) < 0;
          const labels: Label[] = tx.labels || [];
          return (
            <div key={tx.id} className="flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-700 dark:text-foreground truncate">{tx.description || "—"}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-slate-400 dark:text-muted-foreground money">{formatDate(tx.date)}</span>
                  {labels.slice(0, 1).map((l) => (
                    <span
                      key={l.id}
                      className="text-[10px] px-1.5 py-0.5 rounded-full text-white font-medium"
                      style={{ backgroundColor: l.color }}
                    >
                      {l.name}
                    </span>
                  ))}
                </div>
              </div>
              <span className={`text-xs money font-medium whitespace-nowrap ${neg ? "text-danger" : "text-success"}`}>
                {formatMoney(tx.amount)}
              </span>
            </div>
          );
        })}
        {txns.length === 0 && (
          <p className="text-sm text-slate-400 dark:text-muted-foreground">{ex.noTransactions}</p>
        )}
      </div>
    </div>
  );
}
