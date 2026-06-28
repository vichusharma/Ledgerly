"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { translations, type Locale } from "@/lib/i18n/translations";

interface LanguageContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: <K extends keyof typeof translations.fr>(section: K) => typeof translations.fr[K];
}

const LanguageContext = createContext<LanguageContextValue>({
  locale: "fr",
  setLocale: () => {},
  t: (section) => translations.fr[section],
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    const stored = localStorage.getItem("ledgerly-locale") as Locale | null;
    if (stored === "fr" || stored === "en") setLocaleState(stored);
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("ledgerly-locale", l);
  };

  const t = <K extends keyof typeof translations.fr>(section: K) =>
    translations[locale][section] as typeof translations.fr[K];

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);
