/**
 * Money and date formatting for Ledgerly.
 * French convention: 1 234,56 €  (space as thousands sep, comma as decimal)
 */

export type Locale = "fr" | "en";

let _locale: Locale = "fr";

export function setLocale(locale: Locale): void {
  _locale = locale;
}

export function getLocale(): Locale {
  return _locale;
}

/** Format a number as EUR — e.g. 1 234,56 € (fr) or €1,234.56 (en) */
export function formatMoney(
  amount: number | string | null | undefined,
  currency = "EUR",
  locale?: Locale
): string {
  const loc = locale ?? _locale;
  const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
  const intlLocale = loc === "fr" ? "fr-FR" : "en-GB";
  return new Intl.NumberFormat(intlLocale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

/** Format a date — e.g. 28/06/2026 (fr) or 28 Jun 2026 (en) */
export function formatDate(
  date: string | Date | null | undefined,
  locale?: Locale
): string {
  if (!date) return "—";
  const loc = locale ?? _locale;
  const d = typeof date === "string" ? new Date(date) : date;
  const intlLocale = loc === "fr" ? "fr-FR" : "en-GB";
  return new Intl.DateTimeFormat(intlLocale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(d);
}

/** Format a percentage — e.g. 12,34 % (fr) or 12.34% (en) */
export function formatPct(value: number | null | undefined, decimals = 2): string {
  if (value == null) return "—";
  return `${value.toFixed(decimals).replace(".", _locale === "fr" ? "," : ".")} %`;
}

/** Compact large numbers — e.g. 1,2 M€ */
export function formatCompact(amount: number, currency = "EUR", locale?: Locale): string {
  const loc = locale ?? _locale;
  const intlLocale = loc === "fr" ? "fr-FR" : "en-GB";
  return new Intl.NumberFormat(intlLocale, {
    style: "currency",
    currency,
    notation: "compact",
    maximumSignificantDigits: 3,
  }).format(amount);
}
