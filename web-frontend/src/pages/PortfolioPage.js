import AccountBalanceWallet from "@mui/icons-material/AccountBalanceWallet";
import Refresh from "@mui/icons-material/Refresh";
import TrendingDown from "@mui/icons-material/TrendingDown";
import TrendingUp from "@mui/icons-material/TrendingUp";
import {
  Alert,
  Avatar,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Grid,
  IconButton,
  LinearProgress,
  Tab,
  Tabs,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from "recharts";
import AssetAllocator from "../components/AssetAllocator";
import CrossChainDashboard from "../components/CrossChainDashboard";
import { useApp } from "../context/AppContext";
import { usePortfolioData } from "../hooks/useProtocolData";
import { formatCurrency } from "../utils/helpers";

const PageHeader = styled(Box)(({ theme }) => ({
  background:
    theme.palette.mode === "light"
      ? "linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%)"
      : "linear-gradient(135deg, #121212 0%, #1e1e2d 100%)",
  padding: theme.spacing(6, 0, 4),
  marginBottom: theme.spacing(4),
}));

const StatCard = styled(Card)(({ theme }) => ({
  height: "100%",
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
  transition: "transform 0.2s, box-shadow 0.2s",
  "&:hover": {
    transform: "translateY(-4px)",
    boxShadow: theme.shadows[4],
  },
}));

const CHART_DATA = [
  { name: "Jan", value: 18000 },
  { name: "Feb", value: 21000 },
  { name: "Mar", value: 19500 },
  { name: "Apr", value: 23000 },
  { name: "May", value: 22000 },
  { name: "Jun", value: 24850 },
];

const ALLOCATION_COLORS = [
  "#627eea",
  "#f7931a",
  "#2a5ada",
  "#ff007a",
  "#6c63ff",
];

const TabPanel = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const PortfolioPage = () => {
  const theme = useTheme();
  const { user } = useApp();
  const [tab, setTab] = useState(0);
  const walletAddress = user?.wallet_address;

  const { portfolioData, loading, error, refreshPortfolio } =
    usePortfolioData(walletAddress);

  const totalValue = portfolioData?.total_value ?? 0;
  const assets = portfolioData?.assets ?? [];
  const totalChange =
    assets.reduce((sum, a) => sum + (a.change_24h ?? 0), 0) /
    Math.max(assets.length, 1);

  return (
    <Box>
      <PageHeader>
        <Container maxWidth="lg">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                flexWrap: "wrap",
                gap: 2,
              }}
            >
              <Box>
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
                >
                  <AccountBalanceWallet color="primary" />
                  <Typography variant="h4" fontWeight={700}>
                    Portfolio
                  </Typography>
                </Box>
                <Typography variant="body1" color="text.secondary">
                  Track and manage your cross-chain assets
                </Typography>
              </Box>
              <Tooltip title="Refresh portfolio">
                <IconButton onClick={refreshPortfolio} disabled={loading}>
                  {loading ? <CircularProgress size={20} /> : <Refresh />}
                </IconButton>
              </Tooltip>
            </Box>
          </motion.div>
        </Container>
      </PageHeader>

      <Container maxWidth="lg" sx={{ pb: 8 }}>
        {error && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            {error?.message ?? "Unable to reach server - showing demo data."}
          </Alert>
        )}

        {/* Summary Stats */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Value
                </Typography>
                {loading ? (
                  <LinearProgress sx={{ mt: 2 }} />
                ) : (
                  <Typography variant="h5" fontWeight={700} color="primary">
                    {formatCurrency(totalValue)}
                  </Typography>
                )}
              </CardContent>
            </StatCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  24h Change
                </Typography>
                {loading ? (
                  <LinearProgress sx={{ mt: 2 }} />
                ) : (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    {totalChange >= 0 ? (
                      <TrendingUp color="success" />
                    ) : (
                      <TrendingDown color="error" />
                    )}
                    <Typography
                      variant="h5"
                      fontWeight={700}
                      color={totalChange >= 0 ? "success.main" : "error.main"}
                    >
                      {totalChange >= 0 ? "+" : ""}
                      {totalChange.toFixed(2)}%
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </StatCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Assets
                </Typography>
                {loading ? (
                  <LinearProgress sx={{ mt: 2 }} />
                ) : (
                  <Typography variant="h5" fontWeight={700}>
                    {assets.length}
                  </Typography>
                )}
              </CardContent>
            </StatCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Networks
                </Typography>
                {loading ? (
                  <LinearProgress sx={{ mt: 2 }} />
                ) : (
                  <Typography variant="h5" fontWeight={700}>
                    5
                  </Typography>
                )}
              </CardContent>
            </StatCard>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          sx={{ mb: 1, borderBottom: 1, borderColor: "divider" }}
        >
          <Tab label="Overview" />
          <Tab label="Assets" />
          <Tab label="Allocator" />
          <Tab label="Cross-Chain" />
        </Tabs>

        {/* Overview */}
        <TabPanel value={tab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card
                sx={{
                  boxShadow: "none",
                  border: `1px solid ${theme.palette.divider}`,
                }}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Portfolio Performance
                  </Typography>
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={CHART_DATA}>
                      <defs>
                        <linearGradient id="pv" x1="0" y1="0" x2="0" y2="1">
                          <stop
                            offset="5%"
                            stopColor={theme.palette.primary.main}
                            stopOpacity={0.3}
                          />
                          <stop
                            offset="95%"
                            stopColor={theme.palette.primary.main}
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke={theme.palette.divider}
                      />
                      <XAxis
                        dataKey="name"
                        tick={{
                          fill: theme.palette.text.secondary,
                          fontSize: 12,
                        }}
                      />
                      <YAxis
                        tick={{
                          fill: theme.palette.text.secondary,
                          fontSize: 12,
                        }}
                        tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                      />
                      <ChartTooltip
                        formatter={(v) => [`$${v.toLocaleString()}`, "Value"]}
                        contentStyle={{
                          backgroundColor: theme.palette.background.paper,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke={theme.palette.primary.main}
                        fill="url(#pv)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  boxShadow: "none",
                  border: `1px solid ${theme.palette.divider}`,
                  height: "100%",
                }}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Allocation
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={assets}
                        dataKey="value"
                        nameKey="symbol"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                      >
                        {assets.map((_, i) => (
                          <Cell
                            key={i}
                            fill={
                              ALLOCATION_COLORS[i % ALLOCATION_COLORS.length]
                            }
                          />
                        ))}
                      </Pie>
                      <ChartTooltip
                        formatter={(v) => [`$${v.toLocaleString()}`, "Value"]}
                        contentStyle={{
                          backgroundColor: theme.palette.background.paper,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <Box
                    sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}
                  >
                    {assets.map((a, i) => (
                      <Chip
                        key={a.symbol}
                        label={a.symbol}
                        size="small"
                        sx={{
                          bgcolor:
                            ALLOCATION_COLORS[i % ALLOCATION_COLORS.length],
                          color: "white",
                        }}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Assets */}
        <TabPanel value={tab} index={1}>
          <Grid container spacing={2}>
            {loading ? (
              <Grid item xs={12}>
                <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                  <CircularProgress />
                </Box>
              </Grid>
            ) : assets.length === 0 ? (
              <Grid item xs={12}>
                <Box sx={{ textAlign: "center", py: 6 }}>
                  <Typography color="text.secondary">
                    No assets found.
                  </Typography>
                </Box>
              </Grid>
            ) : (
              assets.map((asset, i) => (
                <Grid item xs={12} sm={6} md={4} key={asset.symbol}>
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <Card
                      sx={{
                        boxShadow: "none",
                        border: `1px solid ${theme.palette.divider}`,
                        "&:hover": {
                          boxShadow: theme.shadows[4],
                          transform: "translateY(-4px)",
                        },
                        transition: "all 0.2s",
                      }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1.5,
                            mb: 1.5,
                          }}
                        >
                          <Avatar
                            sx={{
                              bgcolor:
                                ALLOCATION_COLORS[i % ALLOCATION_COLORS.length],
                              width: 40,
                              height: 40,
                            }}
                          >
                            {asset.symbol.slice(0, 2)}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle2" fontWeight={700}>
                              {asset.name}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              {asset.symbol}
                            </Typography>
                          </Box>
                        </Box>
                        <Typography variant="h6" fontWeight={700}>
                          {formatCurrency(asset.value)}
                        </Typography>
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            mt: 0.5,
                          }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            Balance: {asset.balance} {asset.symbol}
                          </Typography>
                          <Chip
                            label={`${(asset.change_24h ?? 0) >= 0 ? "+" : ""}${(asset.change_24h ?? 0).toFixed(2)}%`}
                            size="small"
                            color={
                              (asset.change_24h ?? 0) >= 0 ? "success" : "error"
                            }
                            variant="outlined"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </motion.div>
                </Grid>
              ))
            )}
          </Grid>
        </TabPanel>

        {/* Allocator */}
        <TabPanel value={tab} index={2}>
          <AssetAllocator />
        </TabPanel>

        {/* Cross-Chain */}
        <TabPanel value={tab} index={3}>
          <CrossChainDashboard />
        </TabPanel>
      </Container>
    </Box>
  );
};

export default PortfolioPage;
