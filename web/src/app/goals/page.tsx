"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useGoals, useGoalProgress, useCreateGoal } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { formatMoney, formatDate } from "@/lib/format/money";

function GoalRow({ goal }: { goal: any }) {
  const { data: progress } = useGoalProgress(goal.id);
  const { t } = useLanguage();
  const gx = t("goals");

  return (
    <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-foreground">{goal.name}</h3>
          <p className="text-xs text-slate-400 dark:text-muted-foreground mt-0.5">
            {gx.target} {formatMoney(goal.target_amount)}
            {goal.target_date ? ` · ${formatDate(goal.target_date)}` : ""}
          </p>
        </div>
        {goal.is_achieved && (
          <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full font-medium">
            {gx.achieved}
          </span>
        )}
      </div>

      {progress && (
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-xs text-slate-500 dark:text-muted-foreground">
            <span>{formatMoney(progress.current_value)}</span>
            <span className="font-medium text-slate-700 dark:text-foreground">
              {Math.min(progress.progress_pct, 100).toFixed(1)}%
            </span>
            <span>{formatMoney(progress.target_amount)}</span>
          </div>
          <div className="bg-slate-100 dark:bg-secondary rounded-full h-2.5">
            <div
              className="bg-brand rounded-full h-2.5 transition-all"
              style={{ width: `${Math.min(progress.progress_pct, 100)}%` }}
            />
          </div>
          {progress.projected_reach_date && !progress.on_track && (
            <p className="text-xs text-warning">
              {gx.projection} {formatDate(progress.projected_reach_date)}
            </p>
          )}
          {progress.on_track && !goal.is_achieved && (
            <p className="text-xs text-success">{gx.onTrack}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function GoalsPage() {
  const { data: goals = [] } = useGoals();
  const createGoal = useCreateGoal();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", target_amount: "", target_date: "", type: "other" });
  const { t } = useLanguage();
  const gx = t("goals");

  const handleCreate = async () => {
    await createGoal.mutateAsync({
      name: form.name,
      target_amount: parseFloat(form.target_amount),
      target_date: form.target_date || null,
      type: form.type,
    });
    setShowForm(false);
    setForm({ name: "", target_amount: "", target_date: "", type: "other" });
  };

  const inputClass = "w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";

  return (
    <AppShell>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{gx.title}</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
          >
            {gx.add}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{gx.newGoal}</h3>
            <input
              placeholder={gx.namePlaceholder}
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className={inputClass}
            />
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{gx.targetAmount}</label>
                <input
                  type="number"
                  placeholder="500000"
                  value={form.target_amount}
                  onChange={e => setForm(f => ({ ...f, target_amount: e.target.value }))}
                  className={`mt-1 ${inputClass} money`}
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 dark:text-muted-foreground">{gx.targetDate}</label>
                <input
                  type="date"
                  value={form.target_date}
                  onChange={e => setForm(f => ({ ...f, target_date: e.target.value }))}
                  className={`mt-1 ${inputClass}`}
                />
              </div>
            </div>
            <select
              value={form.type}
              onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
              className={inputClass}
            >
              <option value="fi_number">{gx.types.fi_number}</option>
              <option value="house_payoff">{gx.types.house_payoff}</option>
              <option value="target_portfolio">{gx.types.target_portfolio}</option>
              <option value="other">{gx.types.other}</option>
            </select>
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!form.name || !form.target_amount}
                className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
              >
                {gx.create}
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="text-slate-500 dark:text-muted-foreground text-sm px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-secondary"
              >
                {gx.cancel}
              </button>
            </div>
          </div>
        )}

        {/* Goal list */}
        <div className="space-y-4">
          {goals.map((g: any) => <GoalRow key={g.id} goal={g} />)}
          {goals.length === 0 && (
            <div className="text-center py-12 text-slate-400 dark:text-muted-foreground text-sm">
              {gx.noGoals}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
