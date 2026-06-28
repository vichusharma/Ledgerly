"use client";

import { useState, useRef } from "react";
import { AppShell } from "@/components/AppShell";
import { useAccounts, useImportBatches, useImportMappings } from "@/lib/api/hooks";
import { useLanguage } from "@/lib/context/LanguageContext";
import { apiClient } from "@/lib/api/client";
import { useQueryClient } from "@tanstack/react-query";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";
import { formatDate } from "@/lib/format/money";

export default function ImportPage() {
  const { data: accounts = [] } = useAccounts();
  const { data: batches = [], refetch } = useImportBatches();
  const { data: mappings = [] } = useImportMappings();
  const qc = useQueryClient();
  const { t } = useLanguage();
  const ix = t("import");

  const [selectedAccount, setSelectedAccount] = useState("");
  const [selectedMapping, setSelectedMapping] = useState("");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file || !selectedAccount) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append("file", file);
    form.append("account_id", selectedAccount);
    if (selectedMapping) form.append("mapping_id", selectedMapping);

    try {
      const res = await apiClient.post("/imports/csv", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      refetch();
      qc.invalidateQueries({ queryKey: ["transactions"] });
    } catch (e: any) {
      setError(e.response?.data?.detail || ix.error);
    } finally {
      setUploading(false);
    }
  };

  const selectClass = "mt-1 w-full text-sm border border-surface-border dark:border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20 bg-white dark:bg-secondary dark:text-foreground";

  return (
    <AppShell>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">{ix.title}</h1>

        {/* Upload form */}
        <div className="bg-white dark:bg-card rounded-xl border border-surface-border dark:border-border p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{ix.account}</label>
              <select
                value={selectedAccount}
                onChange={e => setSelectedAccount(e.target.value)}
                className={selectClass}
              >
                <option value="">{ix.selectAccount}</option>
                {accounts.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 dark:text-muted-foreground">{ix.savedMapping}</label>
              <select
                value={selectedMapping}
                onChange={e => setSelectedMapping(e.target.value)}
                className={selectClass}
              >
                <option value="">{ix.autoDetect}</option>
                {mappings.map((m: any) => (
                  <option key={m.id} value={m.id}>{m.institution}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Drop zone */}
          <div
            className="border-2 border-dashed border-slate-200 dark:border-border rounded-xl p-8 text-center cursor-pointer hover:border-brand transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            <Upload className="h-8 w-8 text-slate-300 dark:text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-slate-500 dark:text-muted-foreground">{ix.dropzone}</p>
            <p className="text-xs text-slate-400 dark:text-muted-foreground mt-1">{ix.formats}</p>
            <input ref={fileRef} type="file" accept=".csv" className="hidden" />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-danger bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg px-4 py-3">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          {result && (
            <div className="flex items-center gap-3 text-sm bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-lg px-4 py-3">
              <CheckCircle className="h-5 w-5 text-success" />
              <div>
                <p className="font-medium text-success">{ix.successTitle}</p>
                <p className="text-xs text-slate-500 dark:text-muted-foreground mt-0.5">
                  {result.row_count} {ix.successDesc} · {result.duplicate_count} {ix.duplicates}
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedAccount || uploading}
            className="w-full bg-brand text-white text-sm font-medium py-2.5 rounded-lg disabled:opacity-50 hover:bg-brand-700 transition-colors"
          >
            {uploading ? ix.importing : ix.importBtn}
          </button>
        </div>

        {/* Past imports */}
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
                    <span className="text-xs text-success">✓</span>
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
