"use client";

import { useScope } from "@/lib/hooks/useScope";
import { usePersons } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

export function ScopeToggle() {
  const { scope, setScope } = useScope();
  const { data: persons = [] } = usePersons();

  const options = [
    { value: "household", label: "Foyer" },
    ...persons.map((p: { id: number; name: string }) => ({
      value: String(p.id),
      label: p.name,
    })),
  ];

  return (
    <div className="flex gap-1 bg-slate-100 rounded-md p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => setScope(opt.value)}
          className={cn(
            "flex-1 text-xs font-medium px-2 py-1 rounded transition-colors",
            scope === opt.value
              ? "bg-white text-slate-800 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
