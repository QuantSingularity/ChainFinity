import {
  ArrowForward as ArrowForwardIcon,
  Layers as LayersIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  SwapHoriz as SwapIcon,
  TrendingUp as TrendingUpIcon,
  AccountBalanceWallet as WalletIcon,
} from "@mui/icons-material";
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

const HeroSection = styled(Box)(({ theme }) => ({
  position: "relative",
  padding: theme.spacing(12, 0, 8),
  [theme.breakpoints.down("md")]: {
    padding: theme.spacing(8, 0, 6),
  },
  overflow: "hidden",
  background:
    theme.palette.mode === "light"
      ? "linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%)"
      : "linear-gradient(135deg, #121212 0%, #1e1e2d 100%)",
}));

const FeatureCard = styled(Card)(({ theme }) => ({
  height: "100%",
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2],
  transition: "transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-8px)",
    boxShadow: theme.shadows[8],
  },
}));

const GradientButton = styled(Button)(({ theme }) => ({
  background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
  color: "#ffffff",
  padding: theme.spacing(1.5, 3),
  "&:hover": {
    background: "linear-gradient(45deg, #2a26a0 0%, #4b44b3 100%)",
  },
}));

const OutlinedButton = styled(Button)(({ theme }) => ({
  borderColor: theme.palette.mode === "light" ? "#3a36e0" : "#6c63ff",
  color: theme.palette.mode === "light" ? "#3a36e0" : "#6c63ff",
  padding: theme.spacing(1.5, 3),
  "&:hover": {
    backgroundColor:
      theme.palette.mode === "light"
        ? "rgba(58, 54, 224, 0.08)"
        : "rgba(108, 99, 255, 0.08)",
  },
}));

const FeatureIcon = styled(Avatar)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  width: 56,
  height: 56,
  marginBottom: theme.spacing(2),
}));

const StatsCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
  height: "100%",
}));

const Home = () => {
  const theme = useTheme();
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    // Show success state - email is stored in state and cleared after
    setSubscribed(true);
    setEmail("");
    setTimeout(() => setSubscribed(false), 4000);
    setEmail("");
    // Here you would typically make an API call to subscribe the user
  };

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

  return (
    <Box>
      {/* Hero Section */}
      <HeroSection>
        <Container maxWidth="lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <Grid container spacing={4} alignItems="center">
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <Typography
                    variant="h2"
                    component="h1"
                    fontWeight={700}
                    gutterBottom
                    sx={{
                      background:
                        "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                    }}
                  >
                    Track Your Crypto Portfolio with Ease
                  </Typography>
                  <Typography variant="h6" color="text.secondary" paragraph>
                    ChainFinity is a powerful blockchain portfolio tracker and
                    DeFi analytics platform that helps you monitor your assets
                    across multiple chains in one place.
                  </Typography>
                  <Box
                    sx={{
                      mt: 4,
                      display: "flex",
                      gap: 2,
                      flexWrap: { xs: "wrap", sm: "nowrap" },
                    }}
                  >
                    <GradientButton
                      variant="contained"
                      size="large"
                      component={RouterLink}
                      to="/dashboard"
                    >
                      Get Started
                    </GradientButton>
                    <OutlinedButton
                      variant="outlined"
                      size="large"
                      component={RouterLink}
                      to="/login"
                    >
                      Log In
                    </OutlinedButton>
                  </Box>
                </motion.div>
              </Grid>
              <Grid item xs={12} md={6}>
                <motion.div
                  variants={itemVariants}
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    position: "relative",
                  }}
                >
                  <Box
                    component="img"
                    src="/dashboard-preview.png"
                    alt="Dashboard Preview"
                    sx={{
                      width: "100%",
                      maxWidth: 500,
                      height: "auto",
                      borderRadius: 3,
                      boxShadow: "0 20px 40px rgba(0, 0, 0, 0.1)",
                    }}
                  />
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </HeroSection>

      {/* Stats Section */}
      <Box sx={{ py: 6, backgroundColor: theme.palette.background.default }}>
        <Container maxWidth="lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <motion.div variants={itemVariants}>
                  <StatsCard>
                    <Typography variant="h3" fontWeight={700} gutterBottom>
                      10+
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      Supported Blockchains
                    </Typography>
                  </StatsCard>
                </motion.div>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <motion.div variants={itemVariants}>
                  <StatsCard>
                    <Typography variant="h3" fontWeight={700} gutterBottom>
                      5000+
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      Active Users
                    </Typography>
                  </StatsCard>
                </motion.div>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <motion.div variants={itemVariants}>
                  <StatsCard>
                    <Typography variant="h3" fontWeight={700} gutterBottom>
                      $100M+
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      Assets Tracked
                    </Typography>
                  </StatsCard>
                </motion.div>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <motion.div variants={itemVariants}>
                  <StatsCard>
                    <Typography variant="h3" fontWeight={700} gutterBottom>
                      99.9%
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      Uptime
                    </Typography>
                  </StatsCard>
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </Box>

      {/* Features Section */}
      <Box sx={{ py: 8, backgroundColor: theme.palette.background.paper }}>
        <Container maxWidth="lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            <motion.div variants={itemVariants}>
              <Box sx={{ textAlign: "center", mb: 6 }}>
                <Typography
                  variant="h3"
                  component="h2"
                  fontWeight={700}
                  gutterBottom
                >
                  Key Features
                </Typography>
                <Typography
                  variant="h6"
                  color="text.secondary"
                  sx={{ maxWidth: 700, mx: "auto" }}
                >
                  Everything you need to track and manage your crypto portfolio
                  in one place
                </Typography>
              </Box>
            </motion.div>

            <Grid container spacing={4}>
              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <WalletIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        Multi-Chain Support
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Track your assets across multiple blockchains including
                        Ethereum, Polygon, Binance Smart Chain, and more.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <TrendingUpIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        Portfolio Analytics
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Get detailed insights into your portfolio performance
                        with advanced analytics and visualization tools.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <SwapIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        Transaction History
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        View and filter your complete transaction history across
                        all connected wallets and exchanges.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <SecurityIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        Security First
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Your security is our priority. We use read-only API keys
                        and never store your private keys.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <SpeedIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        Real-Time Data
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Get real-time price updates and portfolio valuation with
                        our high-performance data feeds.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <motion.div variants={itemVariants}>
                  <FeatureCard>
                    <CardContent sx={{ p: 3, textAlign: "center" }}>
                      <FeatureIcon>
                        <LayersIcon />
                      </FeatureIcon>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight={600}
                        gutterBottom
                      >
                        DeFi Integration
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Track your DeFi positions, liquidity pools, and staking
                        rewards all in one dashboard.
                      </Typography>
                    </CardContent>
                  </FeatureCard>
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </Box>

      {/* How It Works Section */}
      <Box sx={{ py: 8, backgroundColor: theme.palette.background.default }}>
        <Container maxWidth="lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            <motion.div variants={itemVariants}>
              <Box sx={{ textAlign: "center", mb: 6 }}>
                <Typography
                  variant="h3"
                  component="h2"
                  fontWeight={700}
                  gutterBottom
                >
                  How It Works
                </Typography>
                <Typography
                  variant="h6"
                  color="text.secondary"
                  sx={{ maxWidth: 700, mx: "auto" }}
                >
                  Get started with ChainFinity in just a few simple steps
                </Typography>
              </Box>
            </motion.div>

            <Grid container spacing={4} alignItems="center">
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <List>
                    <ListItem sx={{ pb: 3 }}>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                          1
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="h6" fontWeight={600}>
                            Create an Account
                          </Typography>
                        }
                        secondary="Sign up for a free ChainFinity account using your email or connect with your wallet."
                      />
                    </ListItem>
                    <ListItem sx={{ pb: 3 }}>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                          2
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="h6" fontWeight={600}>
                            Connect Your Wallets
                          </Typography>
                        }
                        secondary="Add your wallet addresses or connect exchanges using secure API keys."
                      />
                    </ListItem>
                    <ListItem sx={{ pb: 3 }}>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                          3
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="h6" fontWeight={600}>
                            View Your Portfolio
                          </Typography>
                        }
                        secondary="Get a comprehensive overview of all your assets across different blockchains."
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                          4
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="h6" fontWeight={600}>
                            Track Performance
                          </Typography>
                        }
                        secondary="Monitor your portfolio performance, transaction history, and DeFi positions."
                      />
                    </ListItem>
                  </List>
                  <Box sx={{ mt: 4, pl: 9 }}>
                    <GradientButton
                      variant="contained"
                      size="large"
                      component={RouterLink}
                      to="/register"
                      endIcon={<ArrowForwardIcon />}
                    >
                      Get Started Now
                    </GradientButton>
                  </Box>
                </motion.div>
              </Grid>
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <Box
                    component="img"
                    src="/how-it-works.png"
                    alt="How ChainFinity Works"
                    sx={{
                      width: "100%",
                      maxWidth: 500,
                      height: "auto",
                      borderRadius: 3,
                      boxShadow: "0 20px 40px rgba(0, 0, 0, 0.1)",
                      mx: "auto",
                      display: "block",
                    }}
                  />
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Box sx={{ py: 8, backgroundColor: theme.palette.background.paper }}>
        <Container maxWidth="lg">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            <motion.div variants={itemVariants}>
              <Box sx={{ textAlign: "center", mb: 6 }}>
                <Typography
                  variant="h3"
                  component="h2"
                  fontWeight={700}
                  gutterBottom
                >
                  What Our Users Say
                </Typography>
                <Typography
                  variant="h6"
                  color="text.secondary"
                  sx={{ maxWidth: 700, mx: "auto" }}
                >
                  Join thousands of satisfied users who trust ChainFinity for
                  their crypto portfolio tracking
                </Typography>
              </Box>
            </motion.div>

            <Grid container spacing={4}>
              <Grid item xs={12} md={4}>
                <motion.div variants={itemVariants}>
                  <Paper
                    elevation={2}
                    sx={{
                      p: 3,
                      height: "100%",
                      borderRadius: theme.shape.borderRadius,
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    <Typography variant="body1" paragraph>
                      "ChainFinity has completely transformed how I track my
                      crypto investments. The multi-chain support and real-time
                      data are game-changers for anyone serious about their
                      portfolio."
                    </Typography>
                    <Box
                      sx={{
                        mt: "auto",
                        pt: 2,
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      <Avatar sx={{ mr: 2 }}>JD</Avatar>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          John Doe
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Crypto Investor
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </motion.div>
              </Grid>

              <Grid item xs={12} md={4}>
                <motion.div variants={itemVariants}>
                  <Paper
                    elevation={2}
                    sx={{
                      p: 3,
                      height: "100%",
                      borderRadius: theme.shape.borderRadius,
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    <Typography variant="body1" paragraph>
                      "As a DeFi enthusiast, I needed a tool that could track
                      all my positions across different protocols. ChainFinity
                      does this perfectly, saving me hours of manual tracking
                      every week."
                    </Typography>
                    <Box
                      sx={{
                        mt: "auto",
                        pt: 2,
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      <Avatar sx={{ mr: 2 }}>JS</Avatar>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          Jane Smith
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          DeFi Developer
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </motion.div>
              </Grid>

              <Grid item xs={12} md={4}>
                <motion.div variants={itemVariants}>
                  <Paper
                    elevation={2}
                    sx={{
                      p: 3,
                      height: "100%",
                      borderRadius: theme.shape.borderRadius,
                      display: "flex",
                      flexDirection: "column",
                    }}
                  >
                    <Typography variant="body1" paragraph>
                      "The analytics and visualization tools in ChainFinity are
                      unmatched. I can finally understand my portfolio
                      performance at a glance and make informed investment
                      decisions."
                    </Typography>
                    <Box
                      sx={{
                        mt: "auto",
                        pt: 2,
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      <Avatar sx={{ mr: 2 }}>RJ</Avatar>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          Robert Johnson
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Financial Analyst
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          py: 8,
          background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
          color: "white",
        }}
      >
        <Container maxWidth="md">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
          >
            <motion.div variants={itemVariants}>
              <Box sx={{ textAlign: "center", mb: 4 }}>
                <Typography
                  variant="h3"
                  component="h2"
                  fontWeight={700}
                  gutterBottom
                >
                  Ready to Take Control of Your Crypto Portfolio?
                </Typography>
                <Typography
                  variant="h6"
                  sx={{ maxWidth: 700, mx: "auto", mb: 4, opacity: 0.9 }}
                >
                  Join thousands of users who trust ChainFinity for their
                  portfolio tracking needs.
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  component={RouterLink}
                  to="/register"
                  sx={{
                    bgcolor: "white",
                    color: "#3a36e0",
                    "&:hover": {
                      bgcolor: "rgba(255, 255, 255, 0.9)",
                    },
                    px: 4,
                    py: 1.5,
                    fontSize: "1.1rem",
                    fontWeight: 600,
                  }}
                >
                  Sign Up for Free
                </Button>
              </Box>
            </motion.div>

            <motion.div variants={itemVariants}>
              <Divider sx={{ my: 6, bgcolor: "rgba(255, 255, 255, 0.2)" }} />

              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Subscribe to Our Newsletter
                </Typography>
                <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
                  Get the latest updates, news, and special offers delivered
                  directly to your inbox.
                </Typography>
                <Box
                  component="form"
                  onSubmit={handleSubscribe}
                  sx={{
                    display: "flex",
                    maxWidth: 500,
                    mx: "auto",
                    flexDirection: { xs: "column", sm: "row" },
                    gap: { xs: 2, sm: 0 },
                  }}
                >
                  <TextField
                    fullWidth
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    variant="outlined"
                    sx={{
                      bgcolor: "rgba(255, 255, 255, 0.1)",
                      borderRadius: "8px 0 0 8px",
                      "& .MuiOutlinedInput-root": {
                        "& fieldset": {
                          borderColor: "rgba(255, 255, 255, 0.3)",
                          borderRight: { sm: 0 },
                        },
                        "&:hover fieldset": {
                          borderColor: "rgba(255, 255, 255, 0.5)",
                        },
                        "&.Mui-focused fieldset": {
                          borderColor: "white",
                        },
                      },
                      "& .MuiInputBase-input": {
                        color: "white",
                      },
                      "& .MuiInputBase-input::placeholder": {
                        color: "rgba(255, 255, 255, 0.7)",
                        opacity: 1,
                      },
                    }}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    sx={{
                      bgcolor: "white",
                      color: "#3a36e0",
                      "&:hover": {
                        bgcolor: "rgba(255, 255, 255, 0.9)",
                      },
                      borderRadius: { xs: "8px", sm: "0 8px 8px 0" },
                      px: 3,
                    }}
                  >
                    Subscribe
                  </Button>
                </Box>
              </Box>
            </motion.div>
          </motion.div>
        </Container>
      </Box>
    </Box>
  );
};

export default Home;
