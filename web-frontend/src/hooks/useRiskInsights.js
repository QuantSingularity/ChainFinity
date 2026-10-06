import { useCallback, useEffect, useRef, useState } from "react";
import { aiAPI, handleApiError, portfolioAPI, riskAPI } from "../services/api";

const initialState = {
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
  const [state, setState] = useState(initialState);
  const mounted = useRef(true);

  const patch = useCallback((values) => {
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
        const items = portfolioResponse.data?.items || [];
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
      const latest = Array.isArray(assessmentsResponse.data)
        ? assessmentsResponse.data[0] || null
        : null;
      patch({
        insights: insightsResponse.data,
        assessment: latest,
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
    (id) => patch({ portfolioId: id, insights: null, assessment: null }),
    [patch],
  );

  return {
    ...state,
    selectPortfolio,
    refresh: loadInsights,
    runAssessment,
  };
};

export default useRiskInsights;
