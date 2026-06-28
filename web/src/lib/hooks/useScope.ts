/**
 * Global person/household scope context.
 * scope: "household" | "self" | "spouse" | person_id (string)
 */
"use client";

import { createContext, useContext, useState } from "react";

type ScopeValue = "household" | "self" | "spouse" | string;

interface ScopeContextType {
  scope: ScopeValue;
  setScope: (scope: ScopeValue) => void;
}

export const ScopeContext = createContext<ScopeContextType>({
  scope: "household",
  setScope: () => {},
});

export function useScopeProvider() {
  const [scope, setScope] = useState<ScopeValue>("household");
  return { scope, setScope };
}

export function useScope() {
  return useContext(ScopeContext);
}
