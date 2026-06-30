"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, X, RefreshCw } from "lucide-react";
import { useLabels, useLabelRules, useBulkLabels, useRerunRules } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";

// Same palette as the inline label editor on the Expenses page.
const PRESET_COLORS = [
  "#ef4444", "#f97316", "#eab308",
  "#22c55e", "#06b6d4", "#3b82f6",
  "#8b5cf6", "#ec4899", "#6b7280",
];

interface Label { id: number; name: string; color: string }
interface LabelRule { id: number; pattern: string; label_id: number }
interface Row { name: string; color: string; patterns: string[] }

// Multi-value text input: type a pattern, press Enter/comma to add it as a chip.
function PatternInput({
  patterns, onChange, placeholder,
}: { patterns: string[]; onChange: (next: string[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");

  const commit = () => {
    const v = draft.trim();
    if (v && !patterns.includes(v)) onChange([...patterns, v]);
    setDraft("");
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 flex-1 min-w-[14rem] border border-surface-border dark:border-border rounded-lg px-2 py-1.5 bg-white dark:bg-secondary focus-within:ring-2 focus-within:ring-brand/20">
      {patterns.map((p, i) => (
        <span
          key={`${p}-${i}`}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono bg-slate-100 dark:bg-card text-slate-600 dark:text-muted-foreground"
        >
          {p}
          <button
            type="button"
            onClick={() => onChange(patterns.filter((_, idx) => idx !== i))}
            className="opacity-60 hover:opacity-100"
          >
            <X size={10} />
          </button>
        </span>
      ))}
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            commit();
          } else if (e.key === "Backspace" && !draft && patterns.length > 0) {
            onChange(patterns.slice(0, -1));
          }
        }}
        onBlur={commit}
        placeholder={patterns.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[6rem] text-sm font-mono bg-transparent focus:outline-none dark:text-foreground py-0.5"
      />
    </div>
  );
}

export function LabelManager() {
  const { t } = useLanguage();
  const sx = t("settings");

  const { data: labels = [] } = useLabels();
  const { data: rules = [] } = useLabelRules();
  const bulk = useBulkLabels();
  const rerun = useRerunRules();

  const [rows, setRows] = useState<Row[]>([]);
  const [msg, setMsg] = useState("");
  const [rerunMsg, setRerunMsg] = useState("");

  // All rule patterns per label id.
  const patternsByLabel = useMemo(() => {
    const m = new Map<number, string[]>();
    (rules as LabelRule[]).forEach((r) => {
      const arr = m.get(r.label_id) ?? [];
      arr.push(r.pattern);
      m.set(r.label_id, arr);
    });
    return m;
  }, [rules]);

  // Prefill rows from the server once labels + rules have loaded.
  useEffect(() => {
    setRows(
      (labels as Label[]).map((l) => ({
        name: l.name,
        color: l.color,
        patterns: patternsByLabel.get(l.id) ?? [],
      }))
    );
  }, [labels, patternsByLabel]);

  const update = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  const addRow = () =>
    setRows((rs) => [...rs, { name: "", color: PRESET_COLORS[5], patterns: [] }]);

  const removeRow = (i: number) =>
    setRows((rs) => rs.filter((_, idx) => idx !== i));

  const handleSave = async () => {
    const payload = rows
      .filter((r) => r.name.trim())
      .map((r) => ({
        name: r.name.trim(),
        color: r.color,
        patterns: r.patterns,
      }));
    try {
      await bulk.mutateAsync(payload);
      setMsg(sx.labelsSaved);
    } catch {
      setMsg(sx.error);
    }
  };

  const handleRerun = async () => {
    setRerunMsg("");
    try {
      const result = await rerun.mutateAsync();
      setRerunMsg(
        sx.rerunRulesResult
          .replace("{scanned}", String(result.scanned))
          .replace("{categorized}", String(result.categorized))
          .replace("{labeled}", String(result.labeled))
      );
    } catch {
      setRerunMsg(sx.error);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.labelsSection}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{sx.labelsDesc}</p>
      </div>

      {rows.length === 0 && (
        <p className="text-sm text-slate-400 dark:text-muted-foreground">{sx.noLabelsYet}</p>
      )}

      <div className="space-y-2">
        {rows.map((row, i) => (
          <div key={i} className="flex flex-wrap items-center gap-2">
            <input
              value={row.name}
              onChange={(e) => update(i, { name: e.target.value })}
              placeholder={sx.labelName}
              className="w-40 text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground"
            />
            <div className="flex gap-1">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => update(i, { color: c })}
                  className="w-4 h-4 rounded-full transition-transform"
                  style={{
                    backgroundColor: c,
                    outline: row.color === c ? `2px solid ${c}` : "none",
                    outlineOffset: "2px",
                  }}
                />
              ))}
            </div>
            <PatternInput
              patterns={row.patterns}
              onChange={(next) => update(i, { patterns: next })}
              placeholder={sx.labelPattern}
            />
            <button
              type="button"
              onClick={() => removeRow(i)}
              className="text-slate-400 hover:text-danger p-1.5"
              aria-label="remove"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.patternHelp}</p>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={addRow}
          className="inline-flex items-center gap-1.5 text-sm text-brand font-medium hover:underline"
        >
          <Plus size={14} /> {sx.addLabelRow}
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={bulk.isPending}
          className="ml-auto bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
        >
          {sx.saveLabels}
        </button>
      </div>
      {msg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{msg}</p>}

      <div className="flex items-center justify-between gap-3 border-t border-slate-50 dark:border-border pt-4">
        <div>
          <p className="text-sm text-slate-700 dark:text-foreground">{sx.rerunRules}</p>
          <p className="text-xs text-slate-400 dark:text-muted-foreground">{sx.rerunRulesDesc}</p>
        </div>
        <button
          type="button"
          onClick={handleRerun}
          disabled={rerun.isPending}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-brand border border-brand/30 px-3 py-1.5 rounded-lg disabled:opacity-50 hover:bg-brand/5 whitespace-nowrap"
        >
          <RefreshCw size={14} className={rerun.isPending ? "animate-spin" : ""} />
          {rerun.isPending ? sx.rerunRulesRunning : sx.rerunRulesBtn}
        </button>
      </div>
      {rerunMsg && <p className="text-xs text-slate-400 dark:text-muted-foreground">{rerunMsg}</p>}
    </div>
  );
}
