"use client";

// Feature J7-S1 — the app's first reusable numbered-progress component.
// Every existing multi-step flow (salary, import) hand-rolls its own
// `Step` union with no visible progress UI; Epic J's 6-step wizard is
// bigger than any of those and gets this instead.

interface StepIndicatorProps {
  steps: string[];
  currentStep: number; // 0-indexed
  onStepClick?: (index: number) => void; // back-navigation only, never forward
}

export function StepIndicator({ steps, currentStep, onStepClick }: StepIndicatorProps) {
  return (
    <div className="flex items-center w-full">
      {steps.map((label, i) => {
        const isActive = i === currentStep;
        const isDone = i < currentStep;
        const clickable = Boolean(onStepClick) && i < currentStep;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onStepClick?.(i)}
              className={`flex items-center gap-2 ${clickable ? "cursor-pointer" : "cursor-default"}`}
            >
              <span
                className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold shrink-0 transition-colors ${
                  isActive
                    ? "bg-brand text-white"
                    : isDone
                    ? "bg-brand/10 text-brand border border-brand/30"
                    : "bg-slate-100 dark:bg-secondary text-slate-400 dark:text-muted-foreground border border-surface-border dark:border-border"
                }`}
              >
                {i + 1}
              </span>
              <span
                className={`text-xs font-medium hidden sm:inline whitespace-nowrap ${
                  isActive ? "text-slate-900 dark:text-foreground" : "text-slate-400 dark:text-muted-foreground"
                }`}
              >
                {label}
              </span>
            </button>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-px mx-2 ${isDone ? "bg-brand/30" : "bg-surface-border dark:bg-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
