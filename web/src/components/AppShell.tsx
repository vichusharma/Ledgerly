"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, PieChart, CreditCard, Receipt,
  TrendingUp, Target, Wallet, Upload, Settings,
  Command, LogOut, ChevronLeft, ChevronRight, Sun, Moon, Globe,
} from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { ScopeToggle } from "./finance/ScopeToggle";
import { useLogout } from "@/lib/api/hooks";
import { useTheme } from "@/lib/context/ThemeContext";
import { useLanguage } from "@/lib/context/LanguageContext";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const logout = useLogout();
  const { theme, toggleTheme } = useTheme();
  const { locale, setLocale, t } = useLanguage();
  const nav = t("nav");
  const settings = t("settings");

  const NAV_ITEMS = [
    { href: "/dashboard",             icon: LayoutDashboard, label: nav.dashboard },
    { href: "/portfolio",             icon: PieChart,         label: nav.portfolio },
    { href: "/debt",                  icon: CreditCard,       label: nav.debt },
    { href: "/expenses",              icon: Receipt,          label: nav.expenses },
    { href: "/scenarios",             icon: TrendingUp,       label: nav.scenarios },
    { href: "/scenarios/monte-carlo", icon: TrendingUp,       label: nav.monteCarlo },
    { href: "/goals",                 icon: Target,           label: nav.goals },
    { href: "/accounts",              icon: Wallet,           label: nav.accounts },
    { href: "/import",                icon: Upload,           label: nav.import },
    { href: "/settings",              icon: Settings,         label: nav.settings },
  ];

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
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col bg-white dark:bg-card border-r border-surface-border dark:border-border sidebar-transition",
          collapsed ? "w-16" : "w-56"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-14 border-b border-surface-border dark:border-border">
          <div className="w-7 h-7 rounded-lg bg-brand flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            L
          </div>
          {!collapsed && (
            <span className="font-semibold text-slate-800 dark:text-foreground text-sm tracking-tight">Ledgerly</span>
          )}
        </div>

        {/* Scope toggle */}
        {!collapsed && (
          <div className="px-3 py-2 border-b border-surface-border dark:border-border">
            <ScopeToggle />
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/scenarios" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 mx-1 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-50 text-brand-600 dark:bg-indigo-950 dark:text-indigo-400"
                    : "text-slate-600 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary hover:text-slate-900 dark:hover:text-foreground"
                )}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-surface-border dark:border-border p-2 space-y-1">
          {/* Theme + language toggles */}
          {!collapsed ? (
            <div className="flex gap-1 pb-1">
              <button
                onClick={toggleTheme}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
              >
                {theme === "dark"
                  ? <Sun className="h-3.5 w-3.5" />
                  : <Moon className="h-3.5 w-3.5" />}
                <span>{theme === "dark" ? settings.lightMode : settings.darkMode}</span>
              </button>
              <button
                onClick={() => setLocale(locale === "fr" ? "en" : "fr")}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
              >
                <Globe className="h-3.5 w-3.5" />
                <span>{locale === "fr" ? "EN" : "FR"}</span>
              </button>
            </div>
          ) : (
            <>
              <button
                onClick={toggleTheme}
                className="flex items-center justify-center w-full py-2 rounded-md text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
              >
                {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              <button
                onClick={() => setLocale(locale === "fr" ? "en" : "fr")}
                className="flex items-center justify-center w-full py-2 rounded-md text-xs font-semibold text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
              >
                {locale === "fr" ? "EN" : "FR"}
              </button>
            </>
          )}

          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
            title={`${nav.search} (⌘K)`}
          >
            <Command className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <span className="flex items-center gap-2">
                {nav.search}
                <kbd className="text-xs bg-slate-100 dark:bg-secondary border border-slate-200 dark:border-border rounded px-1">⌘K</kbd>
              </span>
            )}
          </button>

          <button
            onClick={() => logout.mutate()}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-500 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
          >
            <LogOut className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>{nav.logout}</span>}
          </button>

          <button
            onClick={() => setCollapsed((c) => !c)}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-slate-400 dark:text-muted-foreground hover:bg-slate-100 dark:hover:bg-secondary transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>{nav.collapse}</span>
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
