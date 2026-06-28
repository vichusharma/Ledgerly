"use client";

import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  LayoutDashboard, PieChart, CreditCard, Receipt,
  TrendingUp, Target, Wallet, Upload, Settings,
} from "lucide-react";
import { useLanguage } from "@/lib/context/LanguageContext";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: Props) {
  const router = useRouter();
  const { t } = useLanguage();
  const cmd = t("command");

  const COMMANDS = [
    { label: cmd.dashboard,   href: "/dashboard",             icon: LayoutDashboard },
    { label: cmd.portfolio,   href: "/portfolio",             icon: PieChart },
    { label: cmd.debt,        href: "/debt",                  icon: CreditCard },
    { label: cmd.expenses,    href: "/expenses",              icon: Receipt },
    { label: cmd.scenarios,   href: "/scenarios",             icon: TrendingUp },
    { label: cmd.monteCarlo,  href: "/scenarios/monte-carlo", icon: TrendingUp },
    { label: cmd.goals,       href: "/goals",                 icon: Target },
    { label: cmd.accounts,    href: "/accounts",              icon: Wallet },
    { label: cmd.import,      href: "/import",                icon: Upload },
    { label: cmd.settings,    href: "/settings",              icon: Settings },
  ];

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
        className="relative w-full max-w-lg bg-white dark:bg-card rounded-xl shadow-2xl border border-slate-200 dark:border-border overflow-hidden animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <div className="flex items-center border-b border-slate-100 dark:border-border px-3">
            <span className="text-slate-400 dark:text-muted-foreground mr-2">⌘</span>
            <Command.Input
              autoFocus
              placeholder={cmd.search}
              className="flex-1 py-3 text-sm outline-none placeholder:text-slate-400 dark:placeholder:text-muted-foreground bg-transparent dark:text-foreground"
            />
            <kbd
              className="text-xs text-slate-400 dark:text-muted-foreground border border-slate-200 dark:border-border rounded px-1.5 py-0.5 cursor-pointer"
              onClick={() => onOpenChange(false)}
            >
              Esc
            </kbd>
          </div>
          <Command.List className="max-h-72 overflow-y-auto p-1">
            <Command.Empty className="py-6 text-center text-sm text-slate-400 dark:text-muted-foreground">
              {cmd.noResults}
            </Command.Empty>
            <Command.Group
              heading={cmd.navigation}
              className="[&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:text-slate-400 dark:[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5"
            >
              {COMMANDS.map((c) => (
                <Command.Item
                  key={c.href}
                  value={c.label}
                  onSelect={() => {
                    router.push(c.href);
                    onOpenChange(false);
                  }}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 dark:text-foreground cursor-pointer
                             aria-selected:bg-brand-50 aria-selected:text-brand-600 dark:aria-selected:bg-indigo-950 dark:aria-selected:text-indigo-400
                             hover:bg-slate-50 dark:hover:bg-secondary"
                >
                  <c.icon className="h-4 w-4 text-slate-400 dark:text-muted-foreground" />
                  {c.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
