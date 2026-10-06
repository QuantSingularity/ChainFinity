import React from "react";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import {
  AppText,
  Badge,
  Button,
  Card,
  EmptyState,
  Screen,
  SectionHeader,
} from "../src/components/ui";
import { useApp } from "../src/context/AppContext";
import { useRiskInsights } from "../src/hooks/useRiskInsights";
import { useTheme } from "../src/theme/ThemeContext";
import { radius, spacing } from "../src/theme/theme";

const BUCKET_TONES = {
  low: "success",
  medium: "brand",
  high: "warning",
  extreme: "error",
} as const;

export const formatPercent = (value: number | null | undefined, digits = 1) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(digits)}%`
    : "n/a";

export const correlationColor = (value: number) => {
  const clamped = Math.max(-1, Math.min(1, Number(value) || 0));
  const alpha = (Math.abs(clamped) * 0.6).toFixed(2);
  return clamped >= 0
    ? `rgba(239, 68, 68, ${alpha})`
    : `rgba(56, 189, 248, ${alpha})`;
};

export default function RiskScreen() {
  const { theme } = useTheme();
  const { isAuthenticated } = useApp();
  const {
    portfolios,
    portfolioId,
    aiStatus,
    insights,
    assessment,
    loading,
    assessing,
    error,
    selectPortfolio,
    refresh,
    runAssessment,
  } = useRiskInsights();

  if (!isAuthenticated) {
    return (
      <Screen>
        <EmptyState
          title="Sign in required"
          subtitle="Please sign in to view risk analytics."
        />
      </Screen>
    );
  }

  const volatility = insights ? Object.entries(insights.volatility) : [];
  const correlation = insights?.correlation ?? null;
  const trained = aiStatus
    ? Object.values(aiStatus.models).filter((m) => m.mode === "trained").length
    : 0;

  return (
    <Screen scroll>
      <ScrollView
        scrollEnabled={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        {aiStatus && (
          <View style={styles.row}>
            <Badge
              label={`${trained} trained model${trained === 1 ? "" : "s"}`}
              tone={trained > 0 ? "success" : "neutral"}
            />
          </View>
        )}

        {portfolios.length > 1 && (
          <View style={styles.chips}>
            {portfolios.map((p) => {
              const active = p.id === portfolioId;
              return (
                <TouchableOpacity
                  key={p.id}
                  accessibilityRole="button"
                  accessibilityLabel={`Select portfolio ${p.name}`}
                  onPress={() => selectPortfolio(p.id)}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: active
                        ? theme.colors.primary
                        : theme.colors.surfaceLight,
                    },
                  ]}
                >
                  <AppText
                    variant="caption"
                    style={{
                      color: active ? "#fff" : theme.colors.textSecondary,
                    }}
                  >
                    {p.name}
                  </AppText>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {error && (
          <Card>
            <AppText color="error">{error.message}</AppText>
          </Card>
        )}

        {!loading && portfolios.length === 0 && !error && (
          <EmptyState
            title="No portfolios"
            subtitle="Create a portfolio with assets to see risk analytics."
          />
        )}

        {insights?.warnings.map((w) => (
          <Card key={w}>
            <AppText variant="caption" color="secondary">
              {w}
            </AppText>
          </Card>
        ))}

        {volatility.length > 0 && (
          <>
            <SectionHeader title="Volatility forecast" />
            {volatility.map(([symbol, f]) => (
              <Card key={symbol}>
                <View style={styles.between}>
                  <AppText variant="h3">{symbol}</AppText>
                  <Badge
                    label={f.vol_bucket}
                    tone={BUCKET_TONES[f.vol_bucket]}
                  />
                </View>
                <AppText variant="h2">{formatPercent(f.predicted_vol)}</AppText>
                <AppText variant="caption" color="secondary">
                  {f.forecast_horizon_days}d forecast, realised{" "}
                  {formatPercent(f.recent_realized_vol)}
                </AppText>
                {f.confidence_interval && (
                  <AppText variant="caption" color="secondary">
                    90% range {formatPercent(f.confidence_interval[0])} to{" "}
                    {formatPercent(f.confidence_interval[1])}
                  </AppText>
                )}
              </Card>
            ))}
          </>
        )}

        {correlation && (
          <>
            <SectionHeader title="Predicted correlations" />
            <Card>
              <View style={styles.matrixRow}>
                <View style={styles.cell} />
                {correlation.assets.map((a) => (
                  <View key={a} style={styles.cell}>
                    <AppText variant="caption" color="secondary">
                      {a}
                    </AppText>
                  </View>
                ))}
              </View>
              {correlation.assets.map((rowAsset, i) => (
                <View key={rowAsset} style={styles.matrixRow}>
                  <View style={styles.cell}>
                    <AppText variant="caption" color="secondary">
                      {rowAsset}
                    </AppText>
                  </View>
                  {correlation.matrix[i].map((value, j) => (
                    <View
                      key={`${rowAsset}-${correlation.assets[j]}`}
                      style={[
                        styles.cell,
                        { backgroundColor: correlationColor(value) },
                      ]}
                    >
                      <AppText variant="caption">{value.toFixed(2)}</AppText>
                    </View>
                  ))}
                </View>
              ))}
            </Card>
          </>
        )}

        {portfolioId !== "" && !loading && (
          <>
            <SectionHeader title="Risk assessment" />
            <Card>
              {assessment ? (
                <>
                  <View style={styles.between}>
                    <AppText variant="h1">
                      {Number(assessment.risk_score).toFixed(1)}
                    </AppText>
                    <View>
                      <Badge label={assessment.risk_level} tone="brand" />
                      {assessment.action_required && (
                        <Badge label="Action required" tone="error" />
                      )}
                    </View>
                  </View>
                  {assessment.recommendations.map((r) => (
                    <AppText key={r} variant="caption" color="secondary">
                      {r}
                    </AppText>
                  ))}
                  {assessment.stress_tests
                    .filter((t) => t.status === "completed")
                    .map((t) => (
                      <View key={t.scenario_name} style={styles.between}>
                        <AppText variant="caption">{t.scenario_name}</AppText>
                        <AppText variant="caption" color="error">
                          {Number(t.potential_loss_percent ?? 0).toFixed(1)}%
                        </AppText>
                      </View>
                    ))}
                </>
              ) : (
                <AppText color="secondary">
                  No assessment yet for this portfolio.
                </AppText>
              )}
              <View style={{ marginTop: spacing.md }}>
                <Button
                  title={assessing ? "Running..." : "Run assessment"}
                  onPress={runAssessment}
                  loading={assessing}
                />
              </View>
            </Card>
          </>
        )}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", marginBottom: spacing.md },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
  },
  between: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  matrixRow: { flexDirection: "row" },
  cell: {
    flex: 1,
    minHeight: 32,
    alignItems: "center",
    justifyContent: "center",
  },
});
