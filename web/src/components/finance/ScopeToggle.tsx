"use client";

import { useScope } from "@/lib/hooks/useScope";
import { usePersons } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { cn } from "@/lib/utils";

export function ScopeToggle() {
  const { scope, setScope } = useScope();
  const { data: persons = [] } = usePersons();
  const { t } = useLanguage();

  const options = [
    { value: "household", label: t("scope").household },
    ...persons.map((p: { id: number; name: string }) => ({
      value: String(p.id),
      label: p.name,
    })),
  ];

  return (
    <div className="flex gap-1 bg-slate-100 dark:bg-secondary rounded-md p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => setScope(opt.value)}
          className={cn(
            "flex-1 text-xs font-medium px-2 py-1 rounded transition-colors",
            scope === opt.value
              ? "bg-white dark:bg-card text-slate-800 dark:text-foreground shadow-sm"
              : "text-slate-500 dark:text-muted-foreground hover:text-slate-700 dark:hover:text-foreground"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
