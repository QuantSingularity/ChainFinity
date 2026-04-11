import {
  AccountBalanceWallet,
  ArrowDownward,
  ArrowUpward,
  MoreVert,
  Refresh,
  SwapHoriz,
  Timeline,
  TrendingUp,
} from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Tab,
  Tabs,
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
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApp } from "../context/AppContext";
import {
  usePortfolioData,
  useTransactionHistory,
} from "../hooks/useProtocolData";

// Styled components
const DashboardCard = styled(Card)(({ theme }) => ({
  height: "100%",
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2],
  transition: "transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-5px)",
    boxShadow: theme.shadows[8],
  },
}));

const StatsCard = styled(Card)(({ theme }) => ({
  height: "100%",
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
  transition: "transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-5px)",
    boxShadow: theme.shadows[4],
  },
}));

const AssetCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
  transition: "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
  "&:hover": {
    transform: "translateY(-3px)",
    boxShadow: theme.shadows[3],
  },
}));

const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

// Sample data for chart
const portfolioData = [
  { name: "Jan", value: 4000 },
  { name: "Feb", value: 3000 },
  { name: "Mar", value: 5000 },
  { name: "Apr", value: 2780 },
  { name: "May", value: 1890 },
  { name: "Jun", value: 2390 },
  { name: "Jul", value: 3490 },
  { name: "Aug", value: 4000 },
  { name: "Sep", value: 5000 },
  { name: "Oct", value: 6000 },
  { name: "Nov", value: 7000 },
  { name: "Dec", value: 9000 },
];

const COLORS = ["#3a36e0", "#6c63ff", "#4caf50", "#ff9800"];

const Dashboard = () => {
  const theme = useTheme();
  const { user } = useApp();
  const [tabValue, setTabValue] = useState(0);

  // Get wallet address from user context
  const walletAddress = user?.wallet_address;

  // Fetch portfolio data and transaction history
  const {
    portfolioData: portfolio,
    loading: portfolioLoading,
    error: portfolioError,
    refreshPortfolio,
  } = usePortfolioData(walletAddress);

  const {
    transactions,
    loading: transactionsLoading,
    error: transactionsError,
    refreshTransactions,
  } = useTransactionHistory(walletAddress);

  // Redirect to login if not authenticated
  const handleTabChange = (_event, newValue) => {
    setTabValue(newValue);
  };

  const handleRefresh = async () => {
    await Promise.all([refreshPortfolio(), refreshTransactions()]);
  };

  // Prepare asset allocation data for pie chart
  const assetAllocation = portfolio?.assets
    ? portfolio.assets.map((asset) => ({
        name: asset.symbol,
        value: parseFloat(asset.balance) * parseFloat(asset.value_usd || 0),
      }))
    : [];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5,
      },
    },
  };

  if (portfolioLoading || transactionsLoading) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <Container maxWidth="lg">
          <LinearProgress color="primary" />
          <Typography variant="h6" sx={{ mt: 2, textAlign: "center" }}>
            Loading your portfolio data...
          </Typography>
        </Container>
      </Box>
    );
  }

  if (portfolioError || transactionsError) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <Container maxWidth="lg">
          <Alert severity="error" sx={{ mb: 2 }}>
            {portfolioError?.message ||
              transactionsError?.message ||
              "An error occurred while loading your data."}
          </Alert>
          <Button
            variant="contained"
            onClick={handleRefresh}
            startIcon={<Refresh />}
          >
            Try Again
          </Button>
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={itemVariants}>
            <Box
              sx={{
                mb: 4,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Box>
                <Typography variant="h4" component="h1" fontWeight={700}>
                  Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Welcome back, {user?.email}! Here's your portfolio overview.
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={handleRefresh}
                sx={{
                  borderRadius: "12px",
                  boxShadow: "none",
                }}
              >
                Refresh
              </Button>
            </Box>
          </motion.div>

          {/* Portfolio Summary */}
          <motion.div variants={itemVariants}>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} md={8}>
                <DashboardCard>
                  <CardContent>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        mb: 2,
                      }}
                    >
                      <Typography variant="h6" fontWeight={600}>
                        Portfolio Value
                      </Typography>
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <Chip
                          icon={<TrendingUp />}
                          label="+12.5% this month"
                          color="success"
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <IconButton size="small">
                          <MoreVert fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                    <Typography
                      variant="h3"
                      component="div"
                      fontWeight={700}
                      sx={{ mb: 1 }}
                    >
                      ${portfolio?.total_value || "0.00"}
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
                      <ArrowUpward
                        color="success"
                        fontSize="small"
                        sx={{ mr: 0.5 }}
                      />
                      <Typography
                        variant="body2"
                        color="success.main"
                        fontWeight={500}
                      >
                        +$1,423.40 (12.5%)
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ ml: 1 }}
                      >
                        vs. last month
                      </Typography>
                    </Box>
                    <Box sx={{ height: 250 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                          data={portfolioData}
                          margin={{
                            top: 5,
                            right: 5,
                            left: 5,
                            bottom: 5,
                          }}
                        >
                          <defs>
                            <linearGradient
                              id="colorValue"
                              x1="0"
                              y1="0"
                              x2="0"
                              y2="1"
                            >
                              <stop
                                offset="5%"
                                stopColor={theme.palette.primary.main}
                                stopOpacity={0.8}
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
                            stroke={theme.palette.text.secondary}
                            tick={{ fontSize: 12 }}
                          />
                          <YAxis
                            stroke={theme.palette.text.secondary}
                            tick={{ fontSize: 12 }}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: theme.palette.background.paper,
                              borderColor: theme.palette.divider,
                              borderRadius: 8,
                              boxShadow: theme.shadows[3],
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.primary.main}
                            fillOpacity={1}
                            fill="url(#colorValue)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </DashboardCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <DashboardCard>
                  <CardContent>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        mb: 2,
                      }}
                    >
                      <Typography variant="h6" fontWeight={600}>
                        Asset Allocation
                      </Typography>
                      <IconButton size="small">
                        <MoreVert fontSize="small" />
                      </IconButton>
                    </Box>
                    <Box
                      sx={{
                        height: 250,
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                      }}
                    >
                      {portfolio?.assets && portfolio.assets.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={assetAllocation}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={80}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {assetAllocation.map((_entry, index) => (
                                <Cell
                                  key={`cell-${index}`}
                                  fill={COLORS[index % COLORS.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip
                              formatter={(value) => [
                                `$${value.toFixed(2)}`,
                                "Value",
                              ]}
                              contentStyle={{
                                backgroundColor: theme.palette.background.paper,
                                borderColor: theme.palette.divider,
                                borderRadius: 8,
                                boxShadow: theme.shadows[3],
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <Typography variant="body1" color="text.secondary">
                          No assets to display
                        </Typography>
                      )}
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Box>
                      {portfolio?.assets?.map((asset, index) => (
                        <Box
                          key={index}
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            mb: 1,
                          }}
                        >
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                            }}
                          >
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: "50%",
                                backgroundColor: COLORS[index % COLORS.length],
                                mr: 1,
                              }}
                            />
                            <Typography variant="body2">
                              {asset.symbol}
                            </Typography>
                          </Box>
                          <Typography variant="body2" fontWeight={500}>
                            $
                            {parseFloat(asset.balance) *
                              parseFloat(asset.value_usd || 0)}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </DashboardCard>
              </Grid>
            </Grid>
          </motion.div>

          {/* Stats Cards */}
          <motion.div variants={itemVariants}>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <Avatar sx={{ bgcolor: "primary.light", mr: 2 }}>
                        <AccountBalanceWallet />
                      </Avatar>
                      <Typography variant="subtitle2" color="text.secondary">
                        Total Assets
                      </Typography>
                    </Box>
                    <Typography variant="h5" fontWeight={600}>
                      {portfolio?.assets?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Across multiple blockchains
                    </Typography>
                  </CardContent>
                </StatsCard>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <Avatar sx={{ bgcolor: "success.light", mr: 2 }}>
                        <TrendingUp />
                      </Avatar>
                      <Typography variant="subtitle2" color="text.secondary">
                        Monthly Gain
                      </Typography>
                    </Box>
                    <Typography variant="h5" fontWeight={600}>
                      +$1,423.40
                    </Typography>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <ArrowUpward
                        color="success"
                        fontSize="small"
                        sx={{ mr: 0.5 }}
                      />
                      <Typography variant="body2" color="success.main">
                        12.5%
                      </Typography>
                    </Box>
                  </CardContent>
                </StatsCard>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <Avatar sx={{ bgcolor: "secondary.light", mr: 2 }}>
                        <SwapHoriz />
                      </Avatar>
                      <Typography variant="subtitle2" color="text.secondary">
                        Transactions
                      </Typography>
                    </Box>
                    <Typography variant="h5" fontWeight={600}>
                      {transactions?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last 30 days
                    </Typography>
                  </CardContent>
                </StatsCard>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <Avatar sx={{ bgcolor: "info.light", mr: 2 }}>
                        <Timeline />
                      </Avatar>
                      <Typography variant="subtitle2" color="text.secondary">
                        Gas Spent
                      </Typography>
                    </Box>
                    <Typography variant="h5" fontWeight={600}>
                      $45.20
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last 30 days
                    </Typography>
                  </CardContent>
                </StatsCard>
              </Grid>
            </Grid>
          </motion.div>

          {/* Assets & Transactions */}
          <motion.div variants={itemVariants}>
            <Paper
              sx={{
                borderRadius: theme.shape.borderRadius,
                overflow: "hidden",
                mb: 4,
              }}
            >
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                sx={{
                  borderBottom: 1,
                  borderColor: "divider",
                  px: 2,
                  "& .MuiTabs-indicator": {
                    height: 3,
                    borderRadius: "3px 3px 0 0",
                  },
                }}
              >
                <Tab label="Assets" />
                <Tab label="Recent Transactions" />
              </Tabs>

              <Box sx={{ p: 3 }}>
                <TabPanel value={tabValue} index={0}>
                  {portfolio?.assets && portfolio.assets.length > 0 ? (
                    portfolio.assets.map((asset, index) => (
                      <AssetCard key={index}>
                        <CardContent sx={{ p: 2 }}>
                          <Grid container alignItems="center">
                            <Grid item xs={1}>
                              <Avatar
                                sx={{
                                  bgcolor: "primary.light",
                                  width: 40,
                                  height: 40,
                                }}
                              >
                                {asset.symbol.charAt(0)}
                              </Avatar>
                            </Grid>
                            <Grid item xs={3} sm={3}>
                              <Typography variant="subtitle1" fontWeight={600}>
                                {asset.symbol}
                              </Typography>
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                {asset.name || asset.symbol}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={3}
                              sm={3}
                              sx={{
                                textAlign: {
                                  xs: "left",
                                  sm: "center",
                                },
                              }}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                Balance
                              </Typography>
                              <Typography variant="subtitle2" fontWeight={600}>
                                {asset.balance} {asset.symbol}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={3}
                              sm={3}
                              sx={{
                                textAlign: {
                                  xs: "right",
                                  sm: "center",
                                },
                              }}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                Value
                              </Typography>
                              <Typography variant="subtitle2" fontWeight={600}>
                                $
                                {(
                                  parseFloat(asset.balance) *
                                  parseFloat(asset.value_usd || 0)
                                ).toFixed(2)}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={2}
                              sm={2}
                              sx={{ textAlign: "right" }}
                            >
                              <Chip
                                label={asset.change || "+0.0%"}
                                color={
                                  asset.change?.startsWith("-")
                                    ? "error"
                                    : "success"
                                }
                                size="small"
                                icon={
                                  asset.change?.startsWith("-") ? (
                                    <ArrowDownward fontSize="small" />
                                  ) : (
                                    <ArrowUpward fontSize="small" />
                                  )
                                }
                              />
                            </Grid>
                          </Grid>
                        </CardContent>
                      </AssetCard>
                    ))
                  ) : (
                    <Box sx={{ textAlign: "center", py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        No assets found in your portfolio
                      </Typography>
                      <Button
                        variant="outlined"
                        sx={{ mt: 2 }}
                        onClick={handleRefresh}
                        startIcon={<Refresh />}
                      >
                        Refresh
                      </Button>
                    </Box>
                  )}
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                  {transactions && transactions.length > 0 ? (
                    transactions.map((tx, index) => (
                      <AssetCard key={index}>
                        <CardContent sx={{ p: 2 }}>
                          <Grid container alignItems="center">
                            <Grid item xs={1}>
                              <Avatar
                                sx={{
                                  bgcolor:
                                    tx.type === "receive"
                                      ? "success.light"
                                      : tx.type === "send"
                                        ? "error.light"
                                        : "info.light",
                                  width: 40,
                                  height: 40,
                                }}
                              >
                                {tx.type === "receive" && <ArrowDownward />}
                                {tx.type === "send" && <ArrowUpward />}
                                {tx.type === "swap" && <SwapHoriz />}
                              </Avatar>
                            </Grid>
                            <Grid item xs={3} sm={3}>
                              <Typography
                                variant="subtitle1"
                                fontWeight={600}
                                sx={{ textTransform: "capitalize" }}
                              >
                                {tx.type}
                              </Typography>
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                {tx.asset}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={3}
                              sm={3}
                              sx={{
                                textAlign: {
                                  xs: "left",
                                  sm: "center",
                                },
                              }}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                Amount
                              </Typography>
                              <Typography variant="subtitle2" fontWeight={600}>
                                {tx.amount}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={3}
                              sm={3}
                              sx={{
                                textAlign: {
                                  xs: "right",
                                  sm: "center",
                                },
                              }}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                Value
                              </Typography>
                              <Typography variant="subtitle2" fontWeight={600}>
                                {tx.value}
                              </Typography>
                            </Grid>
                            <Grid
                              item
                              xs={2}
                              sm={2}
                              sx={{ textAlign: "right" }}
                            >
                              <Chip
                                label={tx.status}
                                color="success"
                                size="small"
                                variant="outlined"
                              />
                            </Grid>
                          </Grid>
                        </CardContent>
                      </AssetCard>
                    ))
                  ) : (
                    <Box sx={{ textAlign: "center", py: 4 }}>
                      <Typography variant="body1" color="text.secondary">
                        No transactions found
                      </Typography>
                      <Button
                        variant="outlined"
                        sx={{ mt: 2 }}
                        onClick={handleRefresh}
                        startIcon={<Refresh />}
                      >
                        Refresh
                      </Button>
                    </Box>
                  )}
                </TabPanel>
              </Box>
            </Paper>
          </motion.div>
        </motion.div>
      </Container>
    </Box>
  );
};

export default Dashboard;
