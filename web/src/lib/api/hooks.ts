/**
 * TanStack Query hooks for every API endpoint.
 * Generated from the FastAPI OpenAPI contract (see scripts/gen_client.sh).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

// ── Auth ─────────────────────────────────────────────────────────────────────

export const useAuthStatus = () =>
  useQuery({
    queryKey: ["auth-status"],
    queryFn: () => apiClient.get("/auth/status").then(r => r.data as { initialized: boolean }),
    staleTime: 0,
    retry: false,
  });

export const useSetupPassword = () =>
  useMutation({
    mutationFn: (password: string) => apiClient.post("/auth/setup", { password }),
  });

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

export const useUpdatePerson = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; [key: string]: unknown }) =>
      apiClient.patch(`/persons/${id}`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["persons"] }),
  });
};

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
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["networth"] });
    },
  });
};

export const useUpdateAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; [k: string]: unknown }) =>
      apiClient.patch(`/accounts/${id}`, data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] });
      // manual_balance can change here, which directly affects net worth.
      qc.invalidateQueries({ queryKey: ["networth"] });
    },
  });
};

export const useArchiveAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/accounts/${id}/archive`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["accounts"] }),
  });
};

// ── Transactions ──────────────────────────────────────────────────────────────

export const useTransactions = (params: Record<string, unknown> = {}) =>
  useQuery({
    queryKey: ["transactions", params],
    queryFn: () => apiClient.get("/transactions", { params }).then(r => r.data),
  });

export const useTransactionAnalytics = (params: Record<string, unknown> = {}) =>
  useQuery({
    queryKey: ["analytics", params],
    queryFn: () => apiClient.get("/transactions/analytics", { params }).then(r => r.data),
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

export const useLabels = () =>
  useQuery({ queryKey: ["labels"], queryFn: () => apiClient.get("/labels").then(r => r.data) });

export const useCreateLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; color: string }) =>
      apiClient.post("/labels", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labels"] }),
  });
};

export const useSetTransactionLabels = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ txnId, labelIds }: { txnId: number; labelIds: number[] }) =>
      apiClient.put(`/transactions/${txnId}/labels`, { label_ids: labelIds }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transactions"] }),
  });
};

export const useUpdateLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; name?: string; color?: string }) =>
      apiClient.patch(`/labels/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labels"] }),
  });
};

export const useDeleteLabel = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/labels/${id}`).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["labels"] });
      qc.invalidateQueries({ queryKey: ["label-rules"] });
    },
  });
};

export const useLabelRules = () =>
  useQuery({ queryKey: ["label-rules"], queryFn: () => apiClient.get("/label-rules").then(r => r.data) });

export const useCreateLabelRule = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { pattern: string; label_id: number; priority?: number }) =>
      apiClient.post("/label-rules", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["label-rules"] }),
  });
};

export const useDeleteLabelRule = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/label-rules/${id}`).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["label-rules"] }),
  });
};

export const useBulkLabels = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (labels: { name: string; color: string; patterns: string[] }[]) =>
      apiClient.post("/labels/bulk", { labels }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["labels"] });
      qc.invalidateQueries({ queryKey: ["label-rules"] });
    },
  });
};

export const useRerunRules = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post("/transactions/rerun-rules").then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["analytics"] });
    },
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

export const useHoldings = (scope = "household") =>
  useQuery({
    queryKey: ["holdings", scope],
    queryFn: () => apiClient.get("/portfolio/holdings", { params: { scope } }).then(r => r.data),
  });

export const useAddHolding = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => apiClient.post("/portfolio/holdings", data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["holdings"] });
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["instruments"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

export const useUpdateHoldingQuantity = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { account_id: number; instrument_id: number; quantity: number }) =>
      apiClient.put("/portfolio/holdings/quantity", data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["holdings"] });
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["networth"] });
    },
  });
};

export const useDeleteLot = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/investment-lots/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["holdings"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

// Modeled as a mutation (not a query) so the add-holding form can call
// .mutateAsync(isin) manually from a debounce effect instead of auto-firing.
export const useInstrumentLookup = () =>
  useMutation({
    mutationFn: (isin: string) =>
      apiClient.get("/instruments/lookup", { params: { isin } }).then(r => r.data),
  });

// Fallback for when an ISIN lookup finds nothing — some funds' ISINs aren't
// indexed by the provider even though the fund is findable by name.
export const useInstrumentSearch = () =>
  useMutation({
    mutationFn: (q: string) =>
      apiClient.get("/instruments/search", { params: { q } }).then(r => r.data),
  });

export const usePriceLookupSetting = () =>
  useQuery({
    queryKey: ["settings", "price-lookup"],
    queryFn: () => apiClient.get("/settings/price-lookup").then(r => r.data),
  });

export const useSetPriceLookupSetting = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) =>
      apiClient.put("/settings/price-lookup", { price_lookup_enabled: enabled }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "price-lookup"] }),
  });
};

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

const invalidateLoan = (
  qc: ReturnType<typeof useQueryClient>, loanId?: number, invalidateNetWorth = true,
) => {
  qc.invalidateQueries({ queryKey: ["loans"] });
  if (loanId) {
    qc.invalidateQueries({ queryKey: ["loans", loanId, "schedule"] });
    qc.invalidateQueries({ queryKey: ["loans", loanId, "summary"] });
  }
  qc.invalidateQueries({ queryKey: ["accounts"] });
  if (invalidateNetWorth) qc.invalidateQueries({ queryKey: ["networth"] });
};

export const useCreateLoan = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: object) => apiClient.post("/liabilities", data).then(r => r.data),
    onSuccess: () => invalidateLoan(qc),
  });
};

export const useUpdateLoan = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; [k: string]: unknown }) =>
      apiClient.patch(`/liabilities/${id}`, data).then(r => r.data),
    // Cosmetic-only edit (name/type/payment_day/institution) — never changes a
    // balance, so no need to refetch net worth.
    onSuccess: (_d, vars) => invalidateLoan(qc, vars.id, false),
  });
};

export const useDeleteLoan = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/liabilities/${id}`),
    onSuccess: () => invalidateLoan(qc),
  });
};

export const usePreviewPrepayment = () =>
  useMutation({
    mutationFn: ({ id, ...data }: { id: number; amount: string; reduction_mode?: string; applied_date?: string }) =>
      apiClient.post(`/liabilities/${id}/prepay/preview`, data).then(r => r.data),
  });

export const useApplyPrepayment = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; amount: string; reduction_mode?: string; applied_date?: string }) =>
      apiClient.post(`/liabilities/${id}/prepay`, data).then(r => r.data),
    onSuccess: (_d, vars) => invalidateLoan(qc, vars.id),
  });
};

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

// ── Pension ───────────────────────────────────────────────────────────────────

export const usePensionProjection = () =>
  useMutation({
    mutationFn: (body: object) =>
      apiClient.post("/pension/project", body).then(r => r.data),
  });

// ── Imports ───────────────────────────────────────────────────────────────────

export const useImportBatches = () =>
  useQuery({ queryKey: ["imports"], queryFn: () => apiClient.get("/imports").then(r => r.data) });

export const useImportMappings = () =>
  useQuery({ queryKey: ["import-mappings"], queryFn: () => apiClient.get("/import/mappings").then(r => r.data) });

// Detect format + return a preview (CSV mapping hints or parsed lines). No DB write.
export const usePreviewStatement = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/imports/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

// Run the import. Invalidates everything a statement can affect.
export const useImportStatement = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/imports/csv", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["imports"] });
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["networth"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["lots"] });
    },
  });
};

// Wrapper valuation statements (AV annual relevés). Preview is read-only.
export const usePreviewValuation = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/imports/pdf-valuation/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useSaveValuation = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      account_id: number;
      as_of_date: string;
      items: { label: string; value: number }[];
    }) => apiClient.post("/imports/pdf-valuation", body).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["networth"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["instruments"] });
    },
  });
};

// ── Salary / payslips ───────────────────────────────────────────────────────

export const usePayslips = (personId?: number, year?: number) =>
  useQuery({
    queryKey: ["payslips", personId, year],
    queryFn: () => {
      const params: Record<string, number> = {};
      if (personId) params.person_id = personId;
      if (year) params.year = year;
      return apiClient.get("/salary/payslips", { params }).then(r => r.data);
    },
  });

// Extract candidate fields from a payslip PDF. No DB write.
export const usePreviewPayslip = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/salary/payslips/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useSavePayslip = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiClient.post("/salary/payslips", body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payslips"] }),
  });
};

export const useDeletePayslip = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/salary/payslips/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payslips"] }),
  });
};

// ── Tax profile (Feature I2 — facts only, no tax computation yet) ──────────

export const useTaxProfile = (personId?: number) =>
  useQuery({
    queryKey: ["tax", "profile", personId],
    queryFn: () => apiClient.get(`/tax/profile/${personId}`).then(r => r.data),
    enabled: personId != null,
  });

export const useSetTaxProfile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ personId, body }: { personId: number; body: object }) =>
      apiClient.put(`/tax/profile/${personId}`, body).then(r => r.data),
    onSuccess: (_data, { personId }) =>
      qc.invalidateQueries({ queryKey: ["tax", "profile", personId] }),
  });
};

export const useHouseholdTaxSettings = () =>
  useQuery({
    queryKey: ["tax", "household-settings"],
    queryFn: () => apiClient.get("/tax/household-settings").then(r => r.data),
  });

export const useSetHouseholdTaxSettings = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) =>
      apiClient.put("/tax/household-settings", body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax", "household-settings"] }),
  });
};

// ── Tax estimate (Feature I3 — salary-only PAS reconciliation) ─────────────

export const useTaxEstimate = (year: number, includeInvestments = false) =>
  useQuery({
    queryKey: ["tax", "estimate", year, includeInvestments],
    queryFn: () =>
      apiClient.get("/tax/estimate", {
        params: { year, include_investments: includeInvestments },
      }).then(r => r.data),
  });

// ── Tax filing — residency & treaties (Feature J1) ──────────────────────────

export const useResidency = (personId?: number) =>
  useQuery({
    queryKey: ["tax-filing", "residency", personId],
    queryFn: () => apiClient.get(`/tax-filing/residency/${personId}`).then(r => r.data),
    enabled: personId != null,
  });

export const useSetResidency = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ personId, body }: { personId: number; body: object }) =>
      apiClient.put(`/tax-filing/residency/${personId}`, body).then(r => r.data),
    onSuccess: (_data, { personId }) =>
      qc.invalidateQueries({ queryKey: ["tax-filing", "residency", personId] }),
  });
};

export const useTreaties = () =>
  useQuery({
    queryKey: ["tax-filing", "treaties"],
    queryFn: () => apiClient.get("/tax-filing/treaties").then(r => r.data),
  });

// ── Tax filing — RSU vesting (Feature J2) ───────────────────────────────────

export const usePreviewRsuVesting = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/rsu-vesting/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useConfirmRsuVesting = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/rsu-vesting", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["tax-filing", "documents"] });
    },
  });
};

// ── Tax filing — ESPP purchases (Feature J2) ────────────────────────────────

export const usePreviewEsppPurchase = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/espp-purchases/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useConfirmEsppPurchase = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/espp-purchases", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lots"] });
      qc.invalidateQueries({ queryKey: ["tax-filing", "documents"] });
    },
  });
};

// ── Tax filing — foreign income, Form 2047 (Feature J2) ─────────────────────

export const useForeignIncome = (personId?: number, taxYear?: number) =>
  useQuery({
    queryKey: ["tax-filing", "foreign-income", personId, taxYear],
    queryFn: () =>
      apiClient.get("/tax-filing/foreign-income", {
        params: { person_id: personId, tax_year: taxYear },
      }).then(r => r.data),
  });

export const usePreviewForeignIncome = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/foreign-income/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useConfirmForeignIncome = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/foreign-income/confirm", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-income"] });
      qc.invalidateQueries({ queryKey: ["tax-filing", "documents"] });
    },
  });
};

export const useCreateForeignIncome = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiClient.post("/tax-filing/foreign-income", body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-income"] }),
  });
};

export const useUpdateForeignIncome = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) =>
      apiClient.put(`/tax-filing/foreign-income/${id}`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-income"] }),
  });
};

export const useDeleteForeignIncome = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/tax-filing/foreign-income/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-income"] }),
  });
};

// ── Tax filing — foreign accounts, Form 3916 (Feature J2) ───────────────────

export const useForeignAccounts = (personId?: number, taxYear?: number) =>
  useQuery({
    queryKey: ["tax-filing", "foreign-accounts", personId, taxYear],
    queryFn: () =>
      apiClient.get("/tax-filing/foreign-accounts", {
        params: { person_id: personId, tax_year: taxYear },
      }).then(r => r.data),
  });

export const usePreviewForeignAccount = () =>
  useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/foreign-accounts/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
  });

export const useConfirmForeignAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiClient.post("/tax-filing/foreign-accounts/confirm", form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-accounts"] });
      qc.invalidateQueries({ queryKey: ["tax-filing", "documents"] });
    },
  });
};

export const useCreateForeignAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => apiClient.post("/tax-filing/foreign-accounts", body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-accounts"] }),
  });
};

export const useUpdateForeignAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) =>
      apiClient.put(`/tax-filing/foreign-accounts/${id}`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-accounts"] }),
  });
};

export const useDeleteForeignAccount = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/tax-filing/foreign-accounts/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "foreign-accounts"] }),
  });
};

// ── Tax filing — encrypted documents (Feature J3) ───────────────────────────

export const useTaxDocuments = (personId?: number, taxYear?: number) =>
  useQuery({
    queryKey: ["tax-filing", "documents", personId, taxYear],
    queryFn: () =>
      apiClient.get("/tax-filing/documents", {
        params: { person_id: personId, tax_year: taxYear },
      }).then(r => r.data),
  });

export const useDownloadTaxDocument = () =>
  useMutation({
    mutationFn: async ({ id, filename }: { id: number; filename: string }) => {
      const res = await apiClient.get(`/tax-filing/documents/${id}/download`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
    },
  });

export const useDeleteTaxDocument = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/tax-filing/documents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tax-filing", "documents"] }),
  });
};

// ── Tax filing — FilingSnapshot compute/validate/lock (Feature J5) ──────────

export const useFilingSnapshot = (year: number) =>
  useQuery({
    queryKey: ["tax-filing", "forms", year],
    queryFn: () => apiClient.get(`/tax-filing/forms/${year}`).then(r => r.data),
    retry: false,
  });

export const useComputeFiling = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (year: number) =>
      apiClient.post("/tax-filing/compute", null, { params: { year } }).then(r => r.data),
    onSuccess: (_data, year) =>
      qc.invalidateQueries({ queryKey: ["tax-filing", "forms", year] }),
  });
};

export const useValidateFiling = () =>
  useMutation({
    mutationFn: (year: number) =>
      apiClient.post("/tax-filing/validate", null, { params: { year } }).then(r => r.data),
  });

export const useLockFiling = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (year: number) =>
      apiClient.post(`/tax-filing/forms/${year}/lock`).then(r => r.data),
    onSuccess: (_data, year) =>
      qc.invalidateQueries({ queryKey: ["tax-filing", "forms", year] }),
  });
};

export const useUnlockFiling = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (year: number) =>
      apiClient.post(`/tax-filing/forms/${year}/unlock`).then(r => r.data),
    onSuccess: (_data, year) =>
      qc.invalidateQueries({ queryKey: ["tax-filing", "forms", year] }),
  });
};

// ── Tax filing — Cerfa-facsimile PDF generation (Feature J6) ────────────────

export const useGenerateFilingPdf = () =>
  useMutation({
    mutationFn: async ({
      year, form, lock,
    }: { year: number; form: "2042" | "2047" | "3916" | "all"; lock?: boolean }) => {
      const res = await apiClient.post("/tax-filing/generate-pdf", null, {
        params: { year, form, lock: lock ?? false },
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = form === "all" ? `ledgerly_filing_${year}.zip` : `${form}_${year}.pdf`;
      a.click();
    },
  });
