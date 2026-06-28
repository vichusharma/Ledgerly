/**
 * TanStack Query hooks for every API endpoint.
 * Generated from the FastAPI OpenAPI contract (see scripts/gen_client.sh).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

// ── Auth ─────────────────────────────────────────────────────────────────────

export const useSession = () =>
  useQuery({ queryKey: ["session"], queryFn: () => apiClient.get("/auth/session").then(r => r.data) });

export const useLogin = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (password: string) => apiClient.post("/auth/login", { password }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["session"] }),
  });
};

export const useLogout = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post("/auth/logout"),
    onSuccess: () => qc.clear(),
  });
};

// ── Persons & accounts ────────────────────────────────────────────────────────

export const usePersons = () =>
  useQuery({ queryKey: ["persons"], queryFn: () => apiClient.get("/persons").then(r => r.data) });

export const useAccounts = (scope = "household", includeArchived = false) =>
  useQuery({
    queryKey: ["accounts", scope, includeArchived],
    queryFn: () =>
      apiClient.get("/accounts", { params: { scope, include_archived: includeArchived } }).then(r => r.data),
  });

export const useCreateAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => apiClient.post("/accounts", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["accounts"] }),
  });
};

// ── Transactions ──────────────────────────────────────────────────────────────

export const useTransactions = (params: Record<string, unknown> = {}) =>
  useQuery({
    queryKey: ["transactions", params],
    queryFn: () => apiClient.get("/transactions", { params }).then(r => r.data),
  });

export const useCategories = () =>
  useQuery({ queryKey: ["categories"], queryFn: () => apiClient.get("/categories").then(r => r.data) });

export const useRules = () =>
  useQuery({ queryKey: ["rules"], queryFn: () => apiClient.get("/rules").then(r => r.data) });

export const useCreateTransaction = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => apiClient.post("/transactions", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transactions"] }),
  });
};

// ── Investments ───────────────────────────────────────────────────────────────

export const useInstruments = () =>
  useQuery({ queryKey: ["instruments"], queryFn: () => apiClient.get("/instruments").then(r => r.data) });

export const useLots = (accountId?: number) =>
  useQuery({
    queryKey: ["lots", accountId],
    queryFn: () =>
      apiClient.get("/investment-lots", { params: accountId ? { account_id: accountId } : {} }).then(r => r.data),
  });

export const usePortfolioPerformance = (scope = "household", wrapper?: string) =>
  useQuery({
    queryKey: ["portfolio", "performance", scope, wrapper],
    queryFn: () =>
      apiClient.get("/portfolio/performance", { params: { scope, wrapper } }).then(r => r.data),
  });

export const usePortfolioAllocation = (scope = "household") =>
  useQuery({
    queryKey: ["portfolio", "allocation", scope],
    queryFn: () =>
      apiClient.get("/portfolio/allocation", { params: { scope } }).then(r => r.data),
  });

// ── Liabilities ───────────────────────────────────────────────────────────────

export const useLoans = () =>
  useQuery({ queryKey: ["loans"], queryFn: () => apiClient.get("/liabilities").then(r => r.data) });

export const useLoanSchedule = (loanId: number) =>
  useQuery({
    queryKey: ["loans", loanId, "schedule"],
    queryFn: () => apiClient.get(`/liabilities/${loanId}/schedule`).then(r => r.data),
    enabled: !!loanId,
  });

export const useLoanSummary = (loanId: number) =>
  useQuery({
    queryKey: ["loans", loanId, "summary"],
    queryFn: () => apiClient.get(`/liabilities/${loanId}/summary`).then(r => r.data),
    enabled: !!loanId,
  });

// ── Net worth ─────────────────────────────────────────────────────────────────

export const useNetWorth = (scope = "household") =>
  useQuery({
    queryKey: ["networth", scope],
    queryFn: () => apiClient.get("/networth", { params: { scope } }).then(r => r.data),
  });

export const useNetWorthSeries = (scope = "household", fromDate?: string, toDate?: string) =>
  useQuery({
    queryKey: ["networth", "series", scope, fromDate, toDate],
    queryFn: () =>
      apiClient.get("/networth/series", { params: { scope, from_date: fromDate, to_date: toDate } }).then(r => r.data),
  });

// ── Scenarios ─────────────────────────────────────────────────────────────────

export const useScenarios = () =>
  useQuery({ queryKey: ["scenarios"], queryFn: () => apiClient.get("/scenarios").then(r => r.data) });

export const useRunScenario = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, params }: { id: number; params: object }) =>
      apiClient.post(`/scenarios/${id}/run`, params).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });
};

// ── Goals ─────────────────────────────────────────────────────────────────────

export const useGoals = () =>
  useQuery({ queryKey: ["goals"], queryFn: () => apiClient.get("/goals").then(r => r.data) });

export const useGoalProgress = (goalId: number) =>
  useQuery({
    queryKey: ["goals", goalId, "progress"],
    queryFn: () => apiClient.get(`/goals/${goalId}/progress`).then(r => r.data),
    enabled: !!goalId,
  });

export const useCreateGoal = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => apiClient.post("/goals", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
};

// ── Imports ───────────────────────────────────────────────────────────────────

export const useImportBatches = () =>
  useQuery({ queryKey: ["imports"], queryFn: () => apiClient.get("/imports").then(r => r.data) });

export const useImportMappings = () =>
  useQuery({ queryKey: ["import-mappings"], queryFn: () => apiClient.get("/import/mappings").then(r => r.data) });
