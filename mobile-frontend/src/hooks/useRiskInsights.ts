import { useCallback, useEffect, useRef, useState } from "react";
import {
  AIStatus,
  aiAPI,
  ApiErrorInfo,
  handleApiError,
  PortfolioAIInsights,
  PortfolioSummary,
  portfolioAPI,
  RiskAssessment,
  riskAPI,
} from "../services/api";

interface RiskInsightsState {
  portfolios: PortfolioSummary[];
  portfolioId: string;
  aiStatus: AIStatus | null;
  insights: PortfolioAIInsights | null;
  assessment: RiskAssessment | null;
  loading: boolean;
  assessing: boolean;
  error: ApiErrorInfo | null;
}

const initialState: RiskInsightsState = {
  portfolios: [],
  portfolioId: "",
  aiStatus: null,
  insights: null,
  assessment: null,
  loading: true,
  assessing: false,
  error: null,
};

export const useRiskInsights = (horizonDays = 7) => {
  const [state, setState] = useState<RiskInsightsState>(initialState);
  const mounted = useRef(true);

  const patch = useCallback((values: Partial<RiskInsightsState>) => {
    if (mounted.current) {
      setState((current) => ({ ...current, ...values }));
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    const bootstrap = async () => {
      try {
        const [portfolioResponse, statusResponse] = await Promise.all([
          portfolioAPI.list(),
          aiAPI.getStatus().catch(() => ({ data: null })),
        ]);
        if (!active) return;
        const items: PortfolioSummary[] = portfolioResponse.data?.items ?? [];
        patch({
          portfolios: items,
          portfolioId: items.length ? items[0].id : "",
          aiStatus: statusResponse.data,
          loading: items.length > 0,
          error: null,
        });
      } catch (error) {
        if (active) patch({ loading: false, error: handleApiError(error) });
      }
    };
    bootstrap();
    return () => {
      active = false;
    };
  }, [patch]);

  const portfolioId = state.portfolioId;

  const loadInsights = useCallback(async () => {
    if (!portfolioId) return;
    patch({ loading: true, error: null });
    try {
      const [insightsResponse, assessmentsResponse] = await Promise.all([
        aiAPI.getPortfolioInsights(portfolioId, horizonDays),
        riskAPI
          .listAssessments({ portfolio_id: portfolioId, limit: 1 })
          .catch(() => ({ data: [] })),
      ]);
      const list = Array.isArray(assessmentsResponse.data)
        ? assessmentsResponse.data
        : [];
      patch({
        insights: insightsResponse.data,
        assessment: list[0] ?? null,
        loading: false,
      });
    } catch (error) {
      patch({ insights: null, loading: false, error: handleApiError(error) });
    }
  }, [portfolioId, horizonDays, patch]);

  useEffect(() => {
    if (portfolioId) loadInsights();
  }, [portfolioId, loadInsights]);

  const runAssessment = useCallback(async () => {
    if (!portfolioId) return;
    patch({ assessing: true, error: null });
    try {
      const response = await riskAPI.assess(portfolioId);
      patch({ assessment: response.data, assessing: false });
    } catch (error) {
      patch({ assessing: false, error: handleApiError(error) });
    }
  }, [portfolioId, patch]);

  const selectPortfolio = useCallback(
    (id: string) =>
      patch({ portfolioId: id, insights: null, assessment: null }),
    [patch],
  );

  return { ...state, selectPortfolio, refresh: loadInsights, runAssessment };
};

export default useRiskInsights;
