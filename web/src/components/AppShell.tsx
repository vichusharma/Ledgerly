"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, PieChart, CreditCard, Receipt,
  TrendingUp, Target, Wallet, Upload, Settings, Landmark, Banknote, Percent,
  Command, LogOut, ChevronLeft, ChevronRight, Sun, Moon, Globe, FileText,
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
    { href: "/pension",               icon: Landmark,         label: nav.pension },
    { href: "/salary",                icon: Banknote,         label: nav.salary },
    { href: "/tax",                   icon: Percent,          label: nav.tax },
    { href: "/tax-filing",            icon: FileText,         label: nav.taxFiling },
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
          <img src="/ledgerly-mark.svg" alt="Ledgerly" className="w-7 h-7 flex-shrink-0" />
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
        <nav className="flex-1 overflow-y-auto py-3 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/scenarios" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex items-center gap-3 px-3 py-2 mx-2 rounded-lg text-sm transition-colors duration-150",
                  collapsed && "justify-center",
                  active
                    ? "bg-brand-50 text-brand-700 font-semibold dark:bg-indigo-500/10 dark:text-indigo-300"
                    : "text-slate-600 dark:text-muted-foreground font-medium hover:bg-slate-100 dark:hover:bg-secondary hover:text-slate-900 dark:hover:text-foreground"
                )}
                title={collapsed ? item.label : undefined}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r-full bg-brand dark:bg-indigo-400" />
                )}
                <item.icon className={cn("h-4 w-4 flex-shrink-0", active && "text-brand dark:text-indigo-400")} />
                {!collapsed && <span className="truncate">{item.label}</span>}
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

          {!collapsed && (
            <p
              title={nav.disclaimerFull}
              className="px-3 pt-2 text-[10px] leading-snug text-slate-400 dark:text-muted-foreground border-t border-surface-border dark:border-border cursor-help"
            >
              {nav.disclaimerShort}
            </p>
          )}
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
