"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, PieChart, CreditCard, Receipt,
  TrendingUp, Target, Wallet, Upload, Settings,
  Command, LogOut, ChevronLeft, ChevronRight,
} from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { ScopeToggle } from "./finance/ScopeToggle";
import { useLogout } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard",  icon: LayoutDashboard, label: "Tableau de bord",  labelEn: "Dashboard" },
  { href: "/portfolio",  icon: PieChart,         label: "Portefeuille",     labelEn: "Portfolio" },
  { href: "/debt",       icon: CreditCard,       label: "Crédits",          labelEn: "Debt" },
  { href: "/expenses",   icon: Receipt,          label: "Dépenses",         labelEn: "Expenses" },
  { href: "/scenarios",       icon: TrendingUp,  label: "Simulateur",       labelEn: "Scenarios" },
  { href: "/scenarios/monte-carlo", icon: TrendingUp, label: "Monte Carlo",   labelEn: "Monte Carlo" },
  { href: "/goals",      icon: Target,           label: "Objectifs",        labelEn: "Goals" },
  { href: "/accounts",   icon: Wallet,           label: "Comptes",          labelEn: "Accounts" },
  { href: "/import",     icon: Upload,           label: "Importer",         labelEn: "Import" },
  { href: "/settings",   icon: Settings,         label: "Paramètres",       labelEn: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const logout = useLogout();

  // ⌘K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col bg-white border-r border-surface-border sidebar-transition",
          collapsed ? "w-16" : "w-56"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-14 border-b border-surface-border">
          <div className="w-7 h-7 rounded-lg bg-brand flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            L
          </div>
          {!collapsed && (
            <span className="font-semibold text-slate-800 text-sm tracking-tight">Ledgerly</span>
          )}
        </div>

        {/* Scope toggle */}
        {!collapsed && (
          <div className="px-3 py-2 border-b border-surface-border">
            <ScopeToggle />
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 mx-1 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-50 text-brand-600"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )}
                title={collapsed ? item.labelEn : undefined}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-surface-border p-2 space-y-1">
          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-500 hover:bg-slate-100 transition-colors"
            title="Command palette (⌘K)"
          >
            <Command className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <span className="flex items-center gap-2">
                Recherche
                <kbd className="text-xs bg-slate-100 border border-slate-200 rounded px-1">⌘K</kbd>
              </span>
            )}
          </button>

          <button
            onClick={() => logout.mutate()}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <LogOut className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>Déconnexion</span>}
          </button>

          <button
            onClick={() => setCollapsed((c) => !c)}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-100 transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Réduire</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* Command Palette */}
      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
    </div>
  );
}
