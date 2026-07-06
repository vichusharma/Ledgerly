"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { AppShell } from "@/components/AppShell";
import {
  usePersons, usePayslips, usePreviewPayslip, useSavePayslip, useDeletePayslip,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { SalaryTrendChart } from "@/components/charts/SalaryTrendChart";
import { formatMoney, formatDate } from "@/lib/format/money";
import { Upload, AlertCircle, CheckCircle, ArrowLeft, ChevronRight, Trash2 } from "lucide-react";

type Step = "upload" | "review" | "done";

interface ReviewState {
  pay_period: string;
  employer: string;
  gross: string;
  net_taxable: string;
  net_before_tax: string;
  net_paid: string;
  pas_rate: string;
  pas_withheld: string;
  ytd_gross: string;
  ytd_net_taxable: string;
  ytd_pas_withheld: string;
}

const BLANK_REVIEW: ReviewState = {
  pay_period: "", employer: "", gross: "", net_taxable: "", net_before_tax: "",
  net_paid: "", pas_rate: "", pas_withheld: "", ytd_gross: "", ytd_net_taxable: "", ytd_pas_withheld: "",
};

const str = (v: unknown) => (v == null ? "" : String(v));

export default function SalaryPage() {
  const { data: persons = [] } = usePersons();
  const { t } = useLanguage();
  const sx = t("salary");

  const [personId, setPersonId] = useState<string>("");
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState<number>(currentYear);

  useEffect(() => {
    if (!personId && persons.length > 0) {
      const primary = persons.find((p: any) => p.is_primary) ?? persons[0];
      setPersonId(String(primary.id));
    }
  }, [persons, personId]);

  const { data: payslips = [] } = usePayslips(personId ? Number(personId) : undefined);
  const previewPayslip = usePreviewPayslip();
  const savePayslip = useSavePayslip();
  const deletePayslip = useDeletePayslip();

  const [step, setStep] = useState<Step>("upload");
  const [review, setReview] = useState<ReviewState>(BLANK_REVIEW);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const setR = (patch: Partial<ReviewState>) => setReview((prev) => ({ ...prev, ...patch }));

  const handleFile = useCallback(async (f: File) => {
    if (!personId) { setError(sx.selectPersonFirst); return; }
    setError(null);

    const form = new FormData();
    form.append("file", f);
    try {
      const preview = await previewPayslip.mutateAsync(form);
      setReview({
        pay_period: preview.pay_period || "",
        employer: preview.employer || "",
        gross: str(preview.gross),
        net_taxable: str(preview.net_taxable),
        net_before_tax: str(preview.net_before_tax),
        net_paid: str(preview.net_paid),
        pas_rate: str(preview.pas_rate),
        pas_withheld: str(preview.pas_withheld),
        ytd_gross: str(preview.ytd_gross),
        ytd_net_taxable: str(preview.ytd_net_taxable),
        ytd_pas_withheld: str(preview.ytd_pas_withheld),
      });
      setStep("review");
    } catch (e: any) {
      setError(e.response?.data?.detail || sx.error);
    }
  }, [personId, sx, previewPayslip]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleBack = () => {
    setStep("upload");
    setReview(BLANK_REVIEW);
    setError(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  const toNum = (v: string) => (v.trim() === "" ? null : Number(v));

  const handleSave = async () => {
    if (!personId || !review.pay_period) return;
    setError(null);
    try {
      await savePayslip.mutateAsync({
        person_id: Number(personId),
        pay_period: review.pay_period,
        employer: review.employer || null,
        gross: toNum(review.gross),
        net_taxable: toNum(review.net_taxable),
        net_before_tax: toNum(review.net_before_tax),
        net_paid: toNum(review.net_paid),
        pas_rate: toNum(review.pas_rate),
        pas_withheld: toNum(review.pas_withheld),
        ytd_gross: toNum(review.ytd_gross),
        ytd_net_taxable: toNum(review.ytd_net_taxable),
        ytd_pas_withheld: toNum(review.ytd_pas_withheld),
      });
      setStep("done");
    } catch (e: any) {
      setError(e.response?.data?.detail || sx.error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm(sx.deleteConfirm)) return;
    await deletePayslip.mutateAsync(id);
  };

  const inputCls = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const labelCls = "block text-xs text-slate-500 dark:text-muted-foreground font-medium";
  const analyzing = previewPayslip.isPending;

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <AppShell>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{sx.title}</h1>
          <p className="text-sm text-slate-500 dark:text-muted-foreground mt-0.5">{sx.subtitle}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>{sx.person}</label>
            <select value={personId} onChange={(e) => setPersonId(e.target.value)} className={inputCls}>
              <option value="">{sx.selectPerson}</option>
              {persons.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>{sx.year}</label>
            <select value={year} onChange={(e) => setYear(Number(e.target.value))} className={inputCls}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {step === "upload" && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-6 space-y-4">
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                personId
                  ? "border-slate-200 dark:border-border cursor-pointer hover:border-brand"
                  : "border-slate-100 dark:border-border/50 opacity-60 cursor-not-allowed"
              }`}
              onClick={() => personId && fileRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
            >
              <Upload className="h-8 w-8 text-slate-300 dark:text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-slate-500 dark:text-muted-foreground">
                {analyzing ? sx.analyzing : sx.uploadDropzone}
              </p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{sx.uploadHint}</p>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              />
            </div>
            {!personId && (
              <p className="text-xs text-slate-400 dark:text-muted-foreground text-center">{sx.selectPersonFirst}</p>
            )}
            {error && (
              <div className="flex items-center gap-2 text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg px-4 py-3">
                <AlertCircle className="h-4 w-4 shrink-0" />{error}
              </div>
            )}
          </div>
        )}

        {step === "review" && (
          <div className="space-y-4">
            <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-6 space-y-5">
              <div>
                <h2 className="text-sm font-semibold text-slate-800 dark:text-foreground">{sx.reviewTitle}</h2>
                <p className="text-xs text-slate-500 dark:text-muted-foreground mt-1">{sx.reviewHint}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>{sx.payPeriod}</label>
                  <input type="date" value={review.pay_period} onChange={(e) => setR({ pay_period: e.target.value })} className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>{sx.employer}</label>
                  <input value={review.employer} onChange={(e) => setR({ employer: e.target.value })} className={inputCls} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {([
                  ["gross", sx.gross], ["net_taxable", sx.netTaxable],
                  ["net_before_tax", sx.netBeforeTax], ["net_paid", sx.netPaid],
                  ["pas_rate", sx.pasRate], ["pas_withheld", sx.pasWithheld],
                ] as [keyof ReviewState, string][]).map(([key, label]) => (
                  <div key={key}>
                    <label className={labelCls}>{label}</label>
                    <input
                      type="number" step="0.01"
                      value={review[key]}
                      onChange={(e) => setR({ [key]: e.target.value } as Partial<ReviewState>)}
                      className={`${inputCls} money`}
                    />
                  </div>
                ))}
              </div>

              <div className="border-t border-surface-border dark:border-border pt-4 grid grid-cols-3 gap-4">
                {([
                  ["ytd_gross", sx.ytdGross], ["ytd_net_taxable", sx.ytdNetTaxable], ["ytd_pas_withheld", sx.ytdPasWithheld],
                ] as [keyof ReviewState, string][]).map(([key, label]) => (
                  <div key={key}>
                    <label className={labelCls}>{label}</label>
                    <input
                      type="number" step="0.01"
                      value={review[key]}
                      onChange={(e) => setR({ [key]: e.target.value } as Partial<ReviewState>)}
                      className={`${inputCls} money`}
                    />
                  </div>
                ))}
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg px-4 py-3">
                <AlertCircle className="h-4 w-4 shrink-0" />{error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleBack}
                className="flex items-center gap-1.5 px-4 py-2.5 text-sm border border-surface-border dark:border-border rounded-lg text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />{sx.backBtn}
              </button>
              <button
                onClick={handleSave}
                disabled={!review.pay_period || savePayslip.isPending}
                className="flex-1 flex items-center justify-center gap-2 bg-brand text-white text-sm font-medium py-2.5 rounded-lg disabled:opacity-50 hover:bg-brand-700 transition-colors"
              >
                {savePayslip.isPending ? sx.saving : (<>{sx.saveBtn}<ChevronRight className="h-4 w-4" /></>)}
              </button>
            </div>
          </div>
        )}

        {step === "done" && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm p-6 space-y-4">
            <div className="flex items-center gap-3 text-sm bg-success/10 border border-success/20 rounded-lg px-4 py-4">
              <CheckCircle className="h-5 w-5 text-success shrink-0" />
              <p className="font-medium text-success">{sx.savedTitle}</p>
            </div>
            <button
              onClick={handleBack}
              className="w-full border border-surface-border dark:border-border text-sm py-2.5 rounded-lg text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary transition-colors"
            >
              {sx.backBtn}
            </button>
          </div>
        )}

        <SalaryTrendChart payslips={payslips} title={sx.trendTitle} />

        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-surface-border dark:border-border">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{sx.historyTitle}</h3>
          </div>
          {payslips.length === 0 ? (
            <p className="px-5 py-6 text-sm text-slate-400 dark:text-muted-foreground text-center">{sx.noPayslips}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-secondary border-b border-surface-border dark:border-border text-slate-400 dark:text-muted-foreground">
                  <th className="px-4 py-2 text-left font-medium">{sx.colPeriod}</th>
                  <th className="px-4 py-2 text-left font-medium">{sx.colEmployer}</th>
                  <th className="px-4 py-2 text-right font-medium">{sx.colGross}</th>
                  <th className="px-4 py-2 text-right font-medium">{sx.colNetTaxable}</th>
                  <th className="px-4 py-2 text-right font-medium">{sx.colNetPaid}</th>
                  <th className="px-4 py-2 text-right font-medium">{sx.colPas}</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {payslips.map((p: any) => (
                  <tr key={p.id} className="border-b border-slate-50 dark:border-border">
                    <td className="px-4 py-2.5 text-slate-700 dark:text-foreground whitespace-nowrap">{formatDate(p.pay_period)}</td>
                    <td className="px-4 py-2.5 text-slate-600 dark:text-muted-foreground max-w-[200px] truncate">{p.employer || "—"}</td>
                    <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">{p.gross != null ? formatMoney(p.gross) : "—"}</td>
                    <td className="px-4 py-2.5 text-right money text-slate-700 dark:text-foreground">{p.net_taxable != null ? formatMoney(p.net_taxable) : "—"}</td>
                    <td className="px-4 py-2.5 text-right money font-medium text-slate-900 dark:text-foreground">{p.net_paid != null ? formatMoney(p.net_paid) : "—"}</td>
                    <td className="px-4 py-2.5 text-right money text-slate-600 dark:text-muted-foreground">{p.pas_withheld != null ? formatMoney(p.pas_withheld) : "—"}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="p-1.5 text-slate-400 hover:text-danger transition-colors"
                        aria-label="delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </AppShell>
  );
}
