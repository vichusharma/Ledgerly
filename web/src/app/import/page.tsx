"use client";

import { useState, useRef, useCallback } from "react";
import { AppShell } from "@/components/AppShell";
import {
  useAccounts, useImportBatches, useImportMappings,
  usePreviewStatement, useImportStatement,
} from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { Upload, CheckCircle, AlertCircle, ChevronRight, ArrowLeft, FileCheck2 } from "lucide-react";
import { formatDate } from "@/lib/format/money";
import { InstitutionCombobox } from "@/components/InstitutionCombobox";

// ── Types ──────────────────────────────────────────────────────────────────────

type Step = "upload" | "mapping" | "done";

interface Preview {
  format: "csv" | "ofx" | "qif" | "camt";
  headers: string[];
  delimiter: string;
  detected: Record<string, string | null>;
  preset_matched: boolean;
  sample: Record<string, string>[];
  sample_txns: { date: string; amount: number; description: string }[];
}

interface Mapping {
  dateCol: string;
  amountMode: "signed" | "split";
  amountCol: string;
  debitCol: string;
  creditCol: string;
  descCol: string;
  delimiter: string;
  dateFormat: string;
  decSep: string;
  saveMapping: boolean;
  institution: string;
}

const BLANK_MAPPING: Mapping = {
  dateCol: "", amountMode: "signed", amountCol: "", debitCol: "", creditCol: "",
  descCol: "", delimiter: ";", dateFormat: "%d/%m/%Y", decSep: ",",
  saveMapping: false, institution: "",
};

export default function ImportPage() {
  const { data: accounts = [] } = useAccounts();
  const { data: batches = [] } = useImportBatches();
  const { data: mappings = [] } = useImportMappings();
  const previewStatement = usePreviewStatement();
  const importStatement = useImportStatement();
  const { t } = useLanguage();
  const ix = t("import");

  const [step, setStep] = useState<Step>("upload");
  const [selectedAccount, setSelectedAccount] = useState("");
  const [selectedMappingId, setSelectedMappingId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [mapping, setMapping] = useState<Mapping>(BLANK_MAPPING);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const setM = (patch: Partial<Mapping>) => setMapping(prev => ({ ...prev, ...patch }));

  const fmtLabel = (f: string) =>
    f === "ofx" ? ix.fmtOfx : f === "qif" ? ix.fmtQif : f === "camt" ? ix.fmtCamt : ix.fmtCsv;

  const handleFile = useCallback(async (f: File) => {
    if (!selectedAccount) { setError(ix.selectAccountFirst); return; }
    setFile(f);
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", f);
    form.append("account_id", selectedAccount);

    try {
      const p: Preview = await previewStatement.mutateAsync(form);
      setPreview(p);

      if (p.format === "csv") {
        // Seed the mapping UI from backend detection (preset-aware),
        // overlaid with an explicitly-selected saved mapping.
        const d = p.detected || {};
        const saved = mappings.find((m: any) => String(m.id) === selectedMappingId);
        const cm = saved?.column_map || {};
        const debit = cm.debit || d.debit || "";
        const credit = cm.credit || d.credit || "";
        const amount = cm.amount || d.amount || "";
        setMapping({
          delimiter: cm.delimiter || p.delimiter || ";",
          dateCol: cm.date || d.date || "",
          amountCol: amount,
          debitCol: debit,
          creditCol: credit,
          descCol: cm.description || d.description || "",
          amountMode: !amount && (debit || credit) ? "split" : "signed",
          dateFormat: saved?.date_format || "%d/%m/%Y",
          decSep: saved?.decimal_separator || ",",
          saveMapping: false,
          institution: "",
        });
      }
      setStep("mapping");
    } catch (e: any) {
      setError(e.response?.data?.detail || ix.error);
    }
  }, [selectedAccount, selectedMappingId, mappings, ix, previewStatement]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const isCsv = preview?.format === "csv";

  const handleImport = async () => {
    if (!file || !selectedAccount) return;
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", file);
    form.append("account_id", selectedAccount);
    if (selectedMappingId) form.append("mapping_id", selectedMappingId);
    // Column config only matters for CSV; the backend ignores it otherwise.
    if (isCsv) {
      if (mapping.dateCol) form.append("date_col", mapping.dateCol);
      if (mapping.amountMode === "signed" && mapping.amountCol) form.append("amount_col", mapping.amountCol);
      if (mapping.amountMode === "split" && mapping.debitCol) form.append("debit_col", mapping.debitCol);
      if (mapping.amountMode === "split" && mapping.creditCol) form.append("credit_col", mapping.creditCol);
      if (mapping.descCol) form.append("desc_col", mapping.descCol);
      form.append("delimiter", mapping.delimiter);
      form.append("date_format", mapping.dateFormat);
      form.append("decimal_separator", mapping.decSep);
      if (mapping.saveMapping && mapping.institution) form.append("save_as", mapping.institution);
    }

    try {
      const data = await importStatement.mutateAsync(form);
      setResult(data);
      setStep("done");
    } catch (e: any) {
      setError(e.response?.data?.detail || ix.error);
    }
  };

  const handleBack = () => {
    setStep("upload");
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const inputCls = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";
  const selectCls = inputCls;
  const labelCls = "block text-xs text-slate-500 dark:text-muted-foreground font-medium";

  const colOptions = (preview?.headers ?? []).map(h => <option key={h} value={h}>{h}</option>);
  const uploading = importStatement.isPending;
  const analyzing = previewStatement.isPending;

  // Canonical "what we'll import" preview, shown for every format.
  const SampleTxns = () => {
    const rows = preview?.sample_txns ?? [];
    if (rows.length === 0) return null;
    return (
      <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-surface-border dark:border-border">
          <p className="text-xs font-medium text-slate-600 dark:text-muted-foreground">{ix.willImportTitle}</p>
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 dark:bg-secondary border-b border-surface-border dark:border-border text-slate-400 dark:text-muted-foreground">
              <th className="px-3 py-2 text-left font-medium">{ix.colDate}</th>
              <th className="px-3 py-2 text-right font-medium">{ix.colAmount}</th>
              <th className="px-3 py-2 text-left font-medium">{ix.colDesc}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-slate-50 dark:border-border">
                <td className="px-3 py-2 text-slate-600 dark:text-foreground whitespace-nowrap">{formatDate(r.date)}</td>
                <td className={`px-3 py-2 text-right whitespace-nowrap money ${Number(r.amount) < 0 ? "text-danger" : "text-success"}`}>
                  {Number(r.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="px-3 py-2 text-slate-600 dark:text-foreground max-w-[280px] truncate">{r.description || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <AppShell>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{ix.title}</h1>

        {/* ── Step 1: Upload ─────────────────────────────────────────────── */}
        {step === "upload" && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>{ix.account}</label>
                <select value={selectedAccount} onChange={e => setSelectedAccount(e.target.value)} className={selectCls}>
                  <option value="">{ix.selectAccount}</option>
                  {accounts.map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>{ix.savedMapping}</label>
                <select value={selectedMappingId} onChange={e => setSelectedMappingId(e.target.value)} className={selectCls}>
                  <option value="">{ix.autoDetect}</option>
                  {mappings.map((m: any) => <option key={m.id} value={m.id}>{m.institution}</option>)}
                </select>
              </div>
            </div>

            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                selectedAccount
                  ? "border-slate-200 dark:border-border cursor-pointer hover:border-brand"
                  : "border-slate-100 dark:border-border/50 opacity-60 cursor-not-allowed"
              }`}
              onClick={() => selectedAccount && fileRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
            >
              <Upload className="h-8 w-8 text-slate-300 dark:text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-slate-500 dark:text-muted-foreground">
                {analyzing ? ix.analyzing : file ? file.name : ix.dropzone}
              </p>
              <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{ix.formats}</p>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.txt,.tsv,.ofx,.qfx,.qif,.xml"
                className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              />
            </div>

            {!selectedAccount && (
              <p className="text-xs text-slate-400 dark:text-muted-foreground text-center">{ix.selectAccountFirst}</p>
            )}
            {error && (
              <div className="flex items-center gap-2 text-sm text-danger bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg px-4 py-3">
                <AlertCircle className="h-4 w-4 shrink-0" />{error}
              </div>
            )}
          </div>
        )}

        {/* ── Step 2: Mapping (CSV) or Confirmation (OFX/QIF/CAMT) ────────── */}
        {step === "mapping" && preview && (
          <div className="space-y-4">
            {/* Format banner */}
            <div className="flex items-center gap-2 text-sm bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg px-4 py-3">
              <FileCheck2 className="h-4 w-4 text-brand shrink-0" />
              <span className="text-slate-700 dark:text-foreground">
                <span className="font-medium">{ix.formatLabel}:</span> {fmtLabel(preview.format)}
              </span>
              {!isCsv && <span className="text-xs text-slate-500 dark:text-muted-foreground ml-1">· {ix.noMappingNeeded}</span>}
              {isCsv && preview.preset_matched && <span className="text-xs text-success ml-1">· {ix.presetApplied}</span>}
            </div>

            {/* CSV mapping controls */}
            {isCsv && (
              <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-6 space-y-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-800 dark:text-foreground">{ix.mapTitle}</h2>
                  <span className="text-xs text-slate-400 dark:text-muted-foreground">{file?.name}</span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={labelCls}>{ix.delimLabel}</label>
                    <select value={mapping.delimiter} onChange={e => setM({ delimiter: e.target.value })} className={selectCls}>
                      <option value=";">; (point-virgule)</option>
                      <option value=",">, (virgule)</option>
                      <option value={"\t"}>⇥ (tabulation)</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelCls}>{ix.dateFormatLabel}</label>
                    <select value={mapping.dateFormat} onChange={e => setM({ dateFormat: e.target.value })} className={selectCls}>
                      <option value="%d/%m/%Y">DD/MM/YYYY</option>
                      <option value="%Y-%m-%d">YYYY-MM-DD</option>
                      <option value="%d-%m-%Y">DD-MM-YYYY</option>
                      <option value="%d.%m.%Y">DD.MM.YYYY</option>
                      <option value="%m/%d/%Y">MM/DD/YYYY</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelCls}>{ix.decSepLabel}</label>
                    <select value={mapping.decSep} onChange={e => setM({ decSep: e.target.value })} className={selectCls}>
                      <option value=",">, (virgule)</option>
                      <option value=".">. (point)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls}>{ix.dateCol}</label>
                    <select value={mapping.dateCol} onChange={e => setM({ dateCol: e.target.value })} className={selectCls}>
                      <option value="">{ix.noColSelected}</option>
                      {colOptions}
                    </select>
                    {!mapping.dateCol && <p className="text-xs text-danger mt-1">{ix.noDateWarning}</p>}
                  </div>
                  <div>
                    <label className={labelCls}>{ix.descCol}</label>
                    <select value={mapping.descCol} onChange={e => setM({ descCol: e.target.value })} className={selectCls}>
                      <option value="">{ix.noColSelected}</option>
                      {colOptions}
                    </select>
                  </div>
                </div>

                <div>
                  <label className={labelCls}>{ix.amountMode}</label>
                  <div className="flex gap-2 mt-1">
                    {(["signed", "split"] as const).map(mode => (
                      <button
                        key={mode}
                        onClick={() => setM({ amountMode: mode })}
                        className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                          mapping.amountMode === mode
                            ? "bg-brand text-white border-brand"
                            : "border-surface-border dark:border-border text-slate-600 dark:text-muted-foreground"
                        }`}
                      >
                        {mode === "signed" ? ix.modeSigned : ix.modeSplitCols}
                      </button>
                    ))}
                  </div>
                </div>

                {mapping.amountMode === "signed" ? (
                  <div>
                    <label className={labelCls}>{ix.amountCol}</label>
                    <select value={mapping.amountCol} onChange={e => setM({ amountCol: e.target.value })} className={selectCls}>
                      <option value="">{ix.noColSelected}</option>
                      {colOptions}
                    </select>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>{ix.debitCol}</label>
                      <select value={mapping.debitCol} onChange={e => setM({ debitCol: e.target.value })} className={selectCls}>
                        <option value="">{ix.noColSelected}</option>
                        {colOptions}
                      </select>
                    </div>
                    <div>
                      <label className={labelCls}>{ix.creditCol}</label>
                      <select value={mapping.creditCol} onChange={e => setM({ creditCol: e.target.value })} className={selectCls}>
                        <option value="">{ix.noColSelected}</option>
                        {colOptions}
                      </select>
                    </div>
                  </div>
                )}

                <div className="border-t border-surface-border dark:border-border pt-4 space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-600 dark:text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={mapping.saveMapping}
                      onChange={e => setM({ saveMapping: e.target.checked })}
                      className="rounded"
                    />
                    {ix.saveMappingLabel}
                  </label>
                  {mapping.saveMapping && (
                    <div>
                      <label className={labelCls}>{ix.institutionLabel}</label>
                      <InstitutionCombobox
                        value={mapping.institution}
                        onChange={val => setM({ institution: val })}
                        placeholder={ix.institutionPlaceholder}
                        inputClass={inputCls}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Canonical preview of the first transactions (all formats) */}
            <SampleTxns />

            {error && (
              <div className="flex items-center gap-2 text-sm text-danger bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg px-4 py-3">
                <AlertCircle className="h-4 w-4 shrink-0" />{error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleBack}
                className="flex items-center gap-1.5 px-4 py-2.5 text-sm border border-surface-border dark:border-border rounded-lg text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />{ix.backBtn}
              </button>
              <button
                onClick={handleImport}
                disabled={(isCsv && !mapping.dateCol) || uploading}
                className="flex-1 flex items-center justify-center gap-2 bg-brand text-white text-sm font-medium py-2.5 rounded-lg disabled:opacity-50 hover:bg-brand-700 transition-colors"
              >
                {uploading ? ix.importing : (<>{ix.importBtn}<ChevronRight className="h-4 w-4" /></>)}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Done ───────────────────────────────────────────────── */}
        {step === "done" && result && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-6 space-y-4">
            <div className="flex items-center gap-3 text-sm bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-lg px-4 py-4">
              <CheckCircle className="h-5 w-5 text-success shrink-0" />
              <div>
                <p className="font-medium text-success">{ix.successTitle}</p>
                <p className="text-xs text-slate-500 dark:text-muted-foreground mt-0.5">
                  {result.row_count} {ix.successDesc} · {result.duplicate_count} {ix.duplicates}
                </p>
              </div>
            </div>
            <button
              onClick={handleBack}
              className="w-full border border-surface-border dark:border-border text-sm py-2.5 rounded-lg text-slate-600 dark:text-muted-foreground hover:bg-slate-50 dark:hover:bg-secondary transition-colors"
            >
              {ix.backBtn}
            </button>
          </div>
        )}

        {/* ── Import history ─────────────────────────────────────────────── */}
        {batches.length > 0 && (
          <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border overflow-hidden">
            <div className="px-5 py-4 border-b border-surface-border dark:border-border">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-foreground">{ix.history}</h3>
            </div>
            <div className="divide-y divide-slate-50 dark:divide-border">
              {batches.map((b: any) => (
                <div key={b.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-700 dark:text-foreground">{b.filename}</p>
                    <p className="text-xs text-slate-400 dark:text-muted-foreground">
                      {formatDate(b.imported_at)} · {b.row_count} {ix.transactions}
                      {b.duplicate_count > 0 ? ` · ${b.duplicate_count} ${ix.duplicates}` : ""}
                    </p>
                  </div>
                  {b.is_rolled_back ? (
                    <span className="text-xs text-slate-400 dark:text-muted-foreground bg-slate-100 dark:bg-secondary px-2 py-0.5 rounded">
                      {ix.cancelled}
                    </span>
                  ) : (
                    <span className={`text-xs font-medium ${b.row_count > 0 ? "text-success" : "text-slate-400 dark:text-muted-foreground"}`}>
                      {b.row_count > 0 ? "✓" : "0"}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
