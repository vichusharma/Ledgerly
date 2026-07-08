"use client";

import { useState } from "react";
import {
  useComputeFiling,
  useFilingSnapshot,
  useValidateFiling,
  useLockFiling,
  useUnlockFiling,
  useGenerateFilingPdf,
} from "@/lib/api/hooks";
import { formatMoney } from "@/lib/format/money";

interface Tf { [key: string]: string }

export function SummaryValidationStep({ year, tf }: { year: number; tf: Tf }) {
  const { data: snapshot, refetch } = useFilingSnapshot(year);
  const compute = useComputeFiling();
  const validate = useValidateFiling();
  const lock = useLockFiling();
  const unlock = useUnlockFiling();
  const generatePdf = useGenerateFilingPdf();
  const [issues, setIssues] = useState<string[] | null>(null);

  const payload = snapshot?.payload;
  const locked = snapshot?.locked ?? false;

  const handleValidate = async () => {
    const result = await validate.mutateAsync(year);
    setIssues(result);
  };

  const handleCompute = async () => {
    await compute.mutateAsync(year);
    refetch();
  };

  const btnCls = "text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50";

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-sm font-semibold text-slate-700 dark:text-foreground">{tf.summaryTitle}</h2>
        <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{tf.summaryDesc}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button onClick={handleCompute} disabled={compute.isPending || locked} className={`${btnCls} bg-brand text-white hover:bg-brand-700`}>
          {tf.recompute}
        </button>
        <button onClick={handleValidate} disabled={validate.isPending} className={`${btnCls} border border-surface-border dark:border-border text-slate-600 dark:text-foreground hover:bg-slate-50 dark:hover:bg-secondary`}>
          {tf.validate}
        </button>
        {locked ? (
          <button onClick={() => unlock.mutate(year)} disabled={unlock.isPending} className={`${btnCls} border border-surface-border dark:border-border text-slate-600 dark:text-foreground hover:bg-slate-50 dark:hover:bg-secondary`}>
            {tf.unlock}
          </button>
        ) : (
          <button onClick={() => lock.mutate(year)} disabled={lock.isPending || !payload} className={`${btnCls} border border-surface-border dark:border-border text-slate-600 dark:text-foreground hover:bg-slate-50 dark:hover:bg-secondary`}>
            {tf.lock}
          </button>
        )}
      </div>

      {locked && (
        <p className="text-xs bg-success/10 text-success px-3 py-2 rounded-lg w-fit">{tf.lockedNotice}</p>
      )}

      {issues && (
        issues.length === 0 ? (
          <p className="text-xs bg-success/10 text-success px-3 py-2 rounded-lg w-fit">{tf.validationClean}</p>
        ) : (
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-lg p-3 space-y-1">
            <p className="text-xs font-semibold text-amber-700 dark:text-amber-400">{tf.validationIssuesTitle}</p>
            <ul className="text-xs text-amber-700 dark:text-amber-400 list-disc pl-4 space-y-0.5">
              {issues.map((issue, i) => <li key={i}>{issue}</li>)}
            </ul>
          </div>
        )
      )}

      {payload && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50 dark:bg-secondary/50 rounded-lg p-3">
              <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.estimatedTax}</p>
              <p className="text-lg font-semibold money">{formatMoney(payload.estimated_tax)}</p>
            </div>
            <div className="bg-slate-50 dark:bg-secondary/50 rounded-lg p-3">
              <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.balance}</p>
              <p className="text-lg font-semibold money">{formatMoney(payload.balance)}</p>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground mb-2">{tf.boxCodesTitle}</h3>
            {payload.boxes_2042.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-muted-foreground">{tf.noBoxes}</p>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {payload.boxes_2042.map((box: any, i: number) => (
                    <tr key={i} className="border-t border-surface-border dark:border-border">
                      <td className="py-1.5 font-mono text-xs text-brand">{box.code}</td>
                      <td className="py-1.5 text-xs text-slate-600 dark:text-foreground">{box.label}</td>
                      <td className="py-1.5 text-right money">{formatMoney(box.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <button onClick={() => generatePdf.mutate({ year, form: "2042" })} disabled={generatePdf.isPending} className={`${btnCls} border border-surface-border dark:border-border hover:bg-slate-50 dark:hover:bg-secondary`}>
              {tf.generate2042}
            </button>
            <button onClick={() => generatePdf.mutate({ year, form: "2047" })} disabled={generatePdf.isPending} className={`${btnCls} border border-surface-border dark:border-border hover:bg-slate-50 dark:hover:bg-secondary`}>
              {tf.generate2047}
            </button>
            <button onClick={() => generatePdf.mutate({ year, form: "3916" })} disabled={generatePdf.isPending} className={`${btnCls} border border-surface-border dark:border-border hover:bg-slate-50 dark:hover:bg-secondary`}>
              {tf.generate3916}
            </button>
            <button onClick={() => generatePdf.mutate({ year, form: "all", lock: true })} disabled={generatePdf.isPending} className={`${btnCls} bg-brand text-white hover:bg-brand-700`}>
              {tf.generateAllAndLock}
            </button>
          </div>

          <div className="bg-slate-50 dark:bg-secondary/50 border border-surface-border dark:border-border rounded-lg p-3 space-y-1">
            <p className="text-xs font-semibold text-slate-600 dark:text-foreground">{tf.disclaimerTitle}</p>
            <p className="text-xs text-slate-500 dark:text-muted-foreground">{tf.disclaimerBody}</p>
            {payload.simplifications_applied.length > 0 && (
              <ul className="text-xs text-slate-500 dark:text-muted-foreground list-disc pl-4 mt-1 space-y-0.5">
                {payload.simplifications_applied.map((key: string) => (
                  <li key={key}>{tf[`simplification_${key}`] ?? key}</li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
