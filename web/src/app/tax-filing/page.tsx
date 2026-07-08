"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { usePersons } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { ResidencyStep } from "@/components/tax-filing/ResidencyStep";
import { ForeignIncomeStep } from "@/components/tax-filing/ForeignIncomeStep";
import { ForeignAccountsStep } from "@/components/tax-filing/ForeignAccountsStep";
import { DeductionsCreditsStep } from "@/components/tax-filing/DeductionsCreditsStep";
import { SummaryValidationStep } from "@/components/tax-filing/SummaryValidationStep";

// Feature J7 — the 6-step wizard the backlog planned (residency ->
// income sources -> foreign income -> foreign accounts ->
// deductions/credits -> summary/validation) is built here as 5 steps:
// Feature J2's RSU/ESPP ("income sources") and foreign-dividend
// ("foreign income") upload flows share identical dropzone+review
// mechanics, so they're consolidated into one ForeignIncomeStep
// component rather than two separate wizard steps — a deliberate
// simplification, not a missed story.
const STEP_COUNT = 5;

export default function TaxFilingPage() {
  const { t } = useLanguage();
  const tf = t("taxFiling");
  const { data: persons = [] } = usePersons();
  const [step, setStep] = useState(0);
  const year = new Date().getFullYear();

  const stepLabels = [
    tf.stepResidency, tf.stepForeignIncome, tf.stepForeignAccounts,
    tf.stepDeductions, tf.stepSummary,
  ];

  const cardCls = "bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-5";

  return (
    <AppShell>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{tf.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{tf.subtitle}</p>
        </div>

        <StepIndicator steps={stepLabels} currentStep={step} onStepClick={setStep} />

        <div className={cardCls}>
          {step === 0 && <ResidencyStep persons={persons} tf={tf} />}
          {step === 1 && <ForeignIncomeStep persons={persons} year={year} tf={tf} />}
          {step === 2 && <ForeignAccountsStep persons={persons} year={year} tf={tf} />}
          {step === 3 && <DeductionsCreditsStep year={year} tf={tf} />}
          {step === 4 && <SummaryValidationStep year={year} tf={tf} />}
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="text-sm font-medium text-slate-500 dark:text-muted-foreground px-4 py-2 rounded-lg disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-secondary"
          >
            {tf.back}
          </button>
          <button
            onClick={() => setStep((s) => Math.min(STEP_COUNT - 1, s + 1))}
            disabled={step === STEP_COUNT - 1}
            className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-40 hover:bg-brand-700"
          >
            {tf.next}
          </button>
        </div>
      </div>
    </AppShell>
  );
}
