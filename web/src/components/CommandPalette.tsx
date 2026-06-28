"use client";

import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  LayoutDashboard, PieChart, CreditCard, Receipt,
  TrendingUp, Target, Wallet, Upload, Settings,
} from "lucide-react";

const COMMANDS = [
  { label: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
  { label: "Portefeuille", href: "/portfolio", icon: PieChart },
  { label: "Crédits & Amortissement", href: "/debt", icon: CreditCard },
  { label: "Dépenses", href: "/expenses", icon: Receipt },
  { label: "Simulateur invest vs. remboursement", href: "/scenarios", icon: TrendingUp },
  { label: "Monte Carlo — projection stochastique", href: "/scenarios/monte-carlo", icon: TrendingUp },
  { label: "Objectifs financiers", href: "/goals", icon: Target },
  { label: "Gérer les comptes", href: "/accounts", icon: Wallet },
  { label: "Importer CSV", href: "/import", icon: Upload },
  { label: "Paramètres", href: "/settings", icon: Settings },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: Props) {
  const router = useRouter();

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] px-4"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        aria-hidden
      />
      <div
        className="relative w-full max-w-lg bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <div className="flex items-center border-b border-slate-100 px-3">
            <span className="text-slate-400 mr-2">⌘</span>
            <Command.Input
              autoFocus
              placeholder="Rechercher…"
              className="flex-1 py-3 text-sm outline-none placeholder:text-slate-400"
            />
            <kbd
              className="text-xs text-slate-400 border border-slate-200 rounded px-1.5 py-0.5 cursor-pointer"
              onClick={() => onOpenChange(false)}
            >
              Esc
            </kbd>
          </div>
          <Command.List className="max-h-72 overflow-y-auto p-1">
            <Command.Empty className="py-6 text-center text-sm text-slate-400">
              Aucun résultat trouvé
            </Command.Empty>
            <Command.Group heading="Navigation">
              {COMMANDS.map((cmd) => (
                <Command.Item
                  key={cmd.href}
                  value={cmd.label}
                  onSelect={() => {
                    router.push(cmd.href);
                    onOpenChange(false);
                  }}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 cursor-pointer
                             aria-selected:bg-brand-50 aria-selected:text-brand-600 hover:bg-slate-50"
                >
                  <cmd.icon className="h-4 w-4 text-slate-400" />
                  {cmd.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
