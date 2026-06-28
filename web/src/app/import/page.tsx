"use client";

import { useState, useRef } from "react";
import { AppShell } from "@/components/AppShell";
import { useAccounts, useImportBatches, useImportMappings } from "@/lib/api/hooks";
import { apiClient } from "@/lib/api/client";
import { useQueryClient } from "@tanstack/react-query";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";
import { formatDate } from "@/lib/format/money";

export default function ImportPage() {
  const { data: accounts = [] } = useAccounts();
  const { data: batches = [], refetch } = useImportBatches();
  const { data: mappings = [] } = useImportMappings();
  const qc = useQueryClient();

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
      setError(e.response?.data?.detail || "Erreur lors de l'importation");
    } finally {
      setUploading(false);
    }
  };

  return (
    <AppShell>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900">Importer un CSV</h1>

        {/* Upload form */}
        <div className="bg-white rounded-xl border border-surface-border p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-500">Compte</label>
              <select
                value={selectedAccount}
                onChange={e => setSelectedAccount(e.target.value)}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
              >
                <option value="">Sélectionner un compte</option>
                {accounts.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500">Mapping sauvegardé</label>
              <select
                value={selectedMapping}
                onChange={e => setSelectedMapping(e.target.value)}
                className="mt-1 w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
              >
                <option value="">Auto-détection</option>
                {mappings.map((m: any) => (
                  <option key={m.id} value={m.id}>{m.institution}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Drop zone */}
          <div
            className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center cursor-pointer hover:border-brand transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            <Upload className="h-8 w-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm text-slate-500">
              Cliquez ou glissez un fichier CSV ici
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Formats supportés : CSV (encodage UTF-8, Latin-1)
            </p>
            <input ref={fileRef} type="file" accept=".csv" className="hidden" />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-danger bg-red-50 border border-red-100 rounded-lg px-4 py-3">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          {result && (
            <div className="flex items-center gap-3 text-sm bg-green-50 border border-green-100 rounded-lg px-4 py-3">
              <CheckCircle className="h-5 w-5 text-success" />
              <div>
                <p className="font-medium text-success">Importation réussie</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {result.row_count} transactions importées · {result.duplicate_count} doublons ignorés
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedAccount || uploading}
            className="w-full bg-brand text-white text-sm font-medium py-2.5 rounded-lg disabled:opacity-50 hover:bg-brand-700 transition-colors"
          >
            {uploading ? "Import en cours…" : "Importer"}
          </button>
        </div>

        {/* Past imports */}
        {batches.length > 0 && (
          <div className="bg-white rounded-xl border border-surface-border overflow-hidden">
            <div className="px-5 py-4 border-b border-surface-border">
              <h3 className="text-sm font-semibold text-slate-700">Historique des imports</h3>
            </div>
            <div className="divide-y divide-slate-50">
              {batches.map((b: any) => (
                <div key={b.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-700">{b.filename}</p>
                    <p className="text-xs text-slate-400">
                      {formatDate(b.imported_at)} · {b.row_count} transactions
                      {b.duplicate_count > 0 ? ` · ${b.duplicate_count} doublons` : ""}
                    </p>
                  </div>
                  {b.is_rolled_back ? (
                    <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">Annulé</span>
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
