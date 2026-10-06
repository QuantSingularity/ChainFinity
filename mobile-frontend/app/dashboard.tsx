import { useRouter } from "expo-router";
import React from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { AllocationBar, RiskRing, Sparkline } from "../src/components/charts";
import {
  AppText,
  Button,
  Card,
  GradientCard,
  Screen,
  SectionHeader,
} from "../src/components/ui";
import { useApp } from "../src/context/AppContext";
import {
  OVERALL_RISK_SCORE,
  PORTFOLIO_HISTORY,
  RISK_METRICS,
} from "../src/hooks/useGovernanceData";
import { PortfolioAsset, usePortfolioData } from "../src/hooks/useProtocolData";
import { useTheme } from "../src/theme/ThemeContext";
import { radius, spacing } from "../src/theme/theme";
import { formatCurrency } from "../src/utils/helpers";

const QUICK_ACTIONS = [
  { label: "Portfolio", route: "/portfolio", icon: "\u25D4" },
  { label: "Risk", route: "/risk", icon: "\u25B2" },
  { label: "Transactions", route: "/transactions", icon: "\u21C4" },
  { label: "Governance", route: "/governance", icon: "\u00A7" },
  { label: "Settings", route: "/settings", icon: "\u2699" },
] as const;

const AssetRow = ({ asset }: { asset: PortfolioAsset }) => {
  const { theme } = useTheme();
  const positive = asset.change_24h >= 0;
  return (
    <View style={styles.assetRow} testID={`asset-${asset.symbol}`}>
      <View style={[styles.assetDot, { backgroundColor: asset.color }]} />
      <View style={{ flex: 1 }}>
        <AppText variant="bodyStrong">{asset.symbol}</AppText>
        <AppText variant="caption" color="secondary">
          {asset.name}
        </AppText>
      </View>
      <View style={{ alignItems: "flex-end" }}>
        <AppText variant="bodyStrong">{formatCurrency(asset.value)}</AppText>
        <Text
          style={{
            fontSize: 12,
            marginTop: 2,
            color: positive ? theme.colors.success : theme.colors.error,
          }}
        >
          {positive ? "+" : ""}
          {asset.change_24h}%
        </Text>
      </View>
    </View>
  );
};

export default function DashboardScreen() {
  const router = useRouter();
  const { user, isAuthenticated } = useApp();
  const { theme } = useTheme();
  const { portfolioData, loading, refreshPortfolio } = usePortfolioData();

  if (!isAuthenticated) {
    return (
      <Screen>
        <View style={styles.center}>
          <AppText color="secondary" center>
            Please sign in to view your dashboard.
          </AppText>
          <Button
            title="Go to Sign In"
            onPress={() => router.replace("/login")}
            fullWidth={false}
            style={{ marginTop: spacing.lg }}
          />
        </View>
      </Screen>
    );
  }

  if (loading && !portfolioData) {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </Screen>
    );
  }

  const assets = portfolioData?.assets ?? [];
  const totalChange = 2.9;
  const slices = assets.map((a) => ({
    label: a.symbol,
    value: a.value,
    color: a.color,
  }));

  return (
    <Screen scroll edges={["bottom"]}>
      <ScrollView
        scrollEnabled={false}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshPortfolio}
            tintColor={theme.colors.primary}
          />
        }
      >
        <AppText color="secondary">
          Welcome{user?.name ? `, ${user.name}` : ""}
        </AppText>

        <GradientCard style={{ marginTop: spacing.md }}>
          <Text style={styles.totalLabel}>Total Portfolio Value</Text>
          <Text style={styles.totalValue} testID="total-value">
            {formatCurrency(portfolioData?.total_value ?? 0)}
          </Text>
          <View style={styles.changeRow}>
            <View style={styles.changePill}>
              <Text style={styles.changeText}>
                {"\u25B2"} {totalChange}% (24h)
              </Text>
            </View>
          </View>
          <View style={{ marginTop: spacing.lg }}>
            <Sparkline data={PORTFOLIO_HISTORY} color="#ffffff" />
          </View>
        </GradientCard>

        <View style={styles.actionsGrid}>
          {QUICK_ACTIONS.map((a) => (
            <TouchableOpacity
              key={a.label}
              style={[
                styles.actionCard,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                },
              ]}
              onPress={() => router.push(a.route)}
              accessibilityRole="button"
              accessibilityLabel={a.label}
            >
              <Text style={{ fontSize: 22 }}>{a.icon}</Text>
              <AppText variant="caption" style={{ marginTop: spacing.xs }}>
                {a.label}
              </AppText>
            </TouchableOpacity>
          ))}
        </View>

        <Card style={{ marginTop: spacing.lg }}>
          <SectionHeader
            title="Risk overview"
            action="Details"
            onAction={() => router.push("/portfolio")}
          />
          <View style={styles.riskRow}>
            <RiskRing score={OVERALL_RISK_SCORE} size={110} />
            <View style={{ flex: 1, marginLeft: spacing.lg }}>
              {RISK_METRICS.map((m) => (
                <View key={m.label} style={{ marginBottom: spacing.sm }}>
                  <View style={styles.metricLabelRow}>
                    <AppText variant="caption" color="secondary">
                      {m.label}
                    </AppText>
                    <AppText variant="caption" color="secondary">
                      {m.value}
                    </AppText>
                  </View>
                  <View style={styles.metricTrack}>
                    <View
                      style={{
                        width: `${m.value}%`,
                        height: "100%",
                        borderRadius: 4,
                        backgroundColor: theme.colors[m.tone],
                      }}
                    />
                  </View>
                </View>
              ))}
            </View>
          </View>
        </Card>

        {slices.length > 0 && (
          <Card style={{ marginTop: spacing.lg }}>
            <SectionHeader title="Allocation" />
            <AllocationBar slices={slices} />
          </Card>
        )}

        <View style={{ marginTop: spacing.lg }}>
          <SectionHeader
            title="Assets"
            action="View all"
            onAction={() => router.push("/portfolio")}
          />
          <Card padded={false} style={{ padding: spacing.xs }}>
            {assets.length === 0 ? (
              <AppText color="secondary" center style={{ padding: spacing.lg }}>
                No assets in this portfolio yet.
              </AppText>
            ) : (
              assets.map((a, i) => (
                <View key={a.symbol}>
                  <View style={{ paddingHorizontal: spacing.md }}>
                    <AssetRow asset={a} />
                  </View>
                  {i < assets.length - 1 && (
                    <View
                      style={[
                        styles.rowDivider,
                        { backgroundColor: theme.colors.divider },
                      ]}
                    />
                  )}
                </View>
              ))
            )}
          </Card>
        </View>

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  totalLabel: { color: "rgba(255,255,255,0.85)", fontSize: 13 },
  totalValue: { color: "#fff", fontSize: 34, fontWeight: "800", marginTop: 6 },
  changeRow: { flexDirection: "row", marginTop: spacing.sm },
  changePill: {
    backgroundColor: "rgba(255,255,255,0.2)",
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: radius.pill,
  },
  changeText: { color: "#fff", fontWeight: "700", fontSize: 12 },
  actionsGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.lg,
    gap: spacing.sm,
  },
  actionCard: {
    flex: 1,
    alignItems: "center",
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  riskRow: { flexDirection: "row", alignItems: "center" },
  metricLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  metricTrack: {
    height: 6,
    borderRadius: 4,
    backgroundColor: "rgba(128,128,160,0.2)",
    overflow: "hidden",
  },
  assetRow: { flexDirection: "row", alignItems: "center", paddingVertical: 14 },
  assetDot: { width: 12, height: 12, borderRadius: 6, marginRight: 12 },
  rowDivider: {
    height: StyleSheet.hairlineWidth,
    marginHorizontal: spacing.md,
  },
});
