"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ScopeContext, useScopeProvider } from "@/lib/hooks/useScope";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            retry: 1,
          },
        },
      })
  );

  const scopeState = useScopeProvider();

  return (
    <QueryClientProvider client={queryClient}>
      <ScopeContext.Provider value={scopeState}>
        {children}
      </ScopeContext.Provider>
    </QueryClientProvider>
  );
}
