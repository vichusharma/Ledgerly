"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { usePersons } from "@/lib/api/hooks";
import { apiClient } from "@/lib/api/client";

export default function SettingsPage() {
  const { data: persons = [], refetch } = usePersons();
  const [newPersonName, setNewPersonName] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const handleAddPerson = async () => {
    if (!newPersonName.trim()) return;
    setSaving(true);
    try {
      await apiClient.post("/persons", {
        name: newPersonName,
        is_primary: persons.length === 0,
      });
      await refetch();
      setNewPersonName("");
      setMsg("Personne ajoutée.");
    } catch {
      setMsg("Erreur.");
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    const res = await apiClient.get("/export", { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ledgerly_export.zip";
    a.click();
  };

  return (
    <AppShell>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-semibold text-slate-900">Paramètres</h1>

        {/* Household members */}
        <section className="bg-white rounded-xl border border-surface-border p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Membres du foyer</h2>
          {persons.length > 0 ? (
            <ul className="space-y-2">
              {persons.map((p: any) => (
                <li key={p.id} className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
                  <div className="w-7 h-7 rounded-full bg-brand-50 text-brand-600 font-semibold text-xs flex items-center justify-center">
                    {p.name[0]}
                  </div>
                  <span className="text-sm text-slate-700">{p.name}</span>
                  {p.is_primary && (
                    <span className="text-xs bg-brand-50 text-brand-600 px-2 py-0.5 rounded-full">Principal</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">Aucun membre — ajoutez-en un ci-dessous</p>
          )}
          <div className="flex gap-2">
            <input
              value={newPersonName}
              onChange={e => setNewPersonName(e.target.value)}
              placeholder="Prénom (ex: Antoine)"
              className="flex-1 text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/20"
            />
            <button
              onClick={handleAddPerson}
              disabled={saving || !newPersonName.trim()}
              className="bg-brand text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 hover:bg-brand-700"
            >
              Ajouter
            </button>
          </div>
          {msg && <p className="text-xs text-slate-400">{msg}</p>}
        </section>

        {/* Data & privacy */}
        <section className="bg-white rounded-xl border border-surface-border p-5 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">Données & confidentialité</h2>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm text-slate-700">Exporter toutes les données</p>
              <p className="text-xs text-slate-400">ZIP contenant JSON + CSV de toutes vos données (RGPD)</p>
            </div>
            <button
              onClick={handleExport}
              className="text-sm text-brand font-medium hover:underline"
            >
              Exporter
            </button>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-slate-50">
            <div>
              <p className="text-sm text-danger">Supprimer toutes les données</p>
              <p className="text-xs text-slate-400">Suppression définitive et irréversible (RGPD)</p>
            </div>
            <button
              onClick={async () => {
                if (confirm("Supprimer TOUTES les données ? Action irréversible.")) {
                  await apiClient.delete("/account/data");
                }
              }}
              className="text-sm text-danger font-medium hover:underline"
            >
              Supprimer
            </button>
          </div>
        </section>

        {/* App info */}
        <section className="bg-white rounded-xl border border-surface-border p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">À propos</h2>
          <dl className="space-y-1 text-sm">
            {[
              ["Application", "Ledgerly v0.1.0"],
              ["Stack", "FastAPI · Next.js 14 · PostgreSQL 16"],
              ["Données", "100% locales — aucune donnée ne quitte votre machine"],
              ["Licence", "MIT"],
            ].map(([k, v]) => (
              <div key={k} className="flex gap-4">
                <dt className="text-slate-400 w-28 flex-shrink-0">{k}</dt>
                <dd className="text-slate-700">{v}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </AppShell>
  );
}
