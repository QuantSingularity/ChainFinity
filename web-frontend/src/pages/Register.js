import {
  AccountBalanceWallet,
  Email,
  Lock,
  Person,
  Visibility,
  VisibilityOff,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  Link,
  Paper,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";

const AuthPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[4],
  [theme.breakpoints.up("md")]: {
    padding: theme.spacing(6),
  },
}));

const AuthContainer = styled(Container)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "calc(100vh - 140px)", // Account for header and footer
  padding: theme.spacing(3),
}));

const AuthDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(3, 0),
  width: "100%",
  position: "relative",
  "&::before": {
    content: '""',
    position: "absolute",
    top: "-8px",
    left: "50%",
    transform: "translateX(-50%)",
    padding: "0 16px",
    backgroundColor: theme.palette.background.paper,
    color: theme.palette.text.secondary,
  },
}));

const SocialButton = styled(Button)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(1.5),
  marginBottom: theme.spacing(2),
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
  "&:hover": {
    boxShadow: theme.shadows[2],
    backgroundColor: theme.palette.background.paper,
  },
}));

const Register = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { register, error, loading, clearError } = useApp();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [formError, setFormError] = useState("");

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleClickShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous errors
    clearError();
    setFormError("");

    // Form validation
    if (!name || !email || !password || !confirmPassword) {
      setFormError("Please fill in all required fields");
      return;
    }

    if (password !== confirmPassword) {
      setFormError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setFormError("Password must be at least 8 characters long");
      return;
    }

    try {
      const result = await register({
        name,
        email,
        password,
        wallet_address: walletAddress || undefined,
      });

      if (result.success) {
        // Redirect to login on success
        navigate("/login", {
          state: {
            message:
              "Registration successful! Please log in with your new account.",
          },
        });
      }
    } catch (_err) {
      setFormError("An unexpected error occurred. Please try again.");
    }
  };

  return (
    <AuthContainer maxWidth="sm">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: "100%" }}
      >
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Typography
            variant="h4"
            component="h1"
            fontWeight={700}
            sx={{
              mb: 1,
              background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Create Account
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Join ChainFinity to track your crypto portfolio
          </Typography>
        </Box>

        <AuthPaper elevation={3}>
          {(error || formError) && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {formError ||
                error?.message ||
                "Registration failed. Please try again."}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Full Name"
              variant="outlined"
              margin="normal"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Person color="action" />
                  </InputAdornment>
                ),
              }}
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Email Address"
              variant="outlined"
              margin="normal"
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email color="action" />
                  </InputAdornment>
                ),
              }}
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Password"
              variant="outlined"
              margin="normal"
              required
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowPassword}
                      onMouseDown={handleMouseDownPassword}
                      edge="end"
                      disabled={loading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Confirm Password"
              variant="outlined"
              margin="normal"
              required
              type={showConfirmPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowConfirmPassword}
                      onMouseDown={handleMouseDownPassword}
                      edge="end"
                      disabled={loading}
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Wallet Address (Optional)"
              variant="outlined"
              margin="normal"
              value={walletAddress}
              onChange={(e) => setWalletAddress(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <AccountBalanceWallet color="action" />
                  </InputAdornment>
                ),
              }}
              disabled={loading}
              helperText="Connect your Ethereum wallet address to track your portfolio"
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              sx={{ py: 1.5, mb: 2, mt: 2 }}
              disabled={loading}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Create Account"
              )}
            </Button>

            <Box sx={{ textAlign: "center", mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?{" "}
                <Link
                  component={RouterLink}
                  to="/login"
                  fontWeight={600}
                  color="primary"
                >
                  Sign In
                </Link>
              </Typography>
            </Box>
          </form>

          <AuthDivider>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                position: "absolute",
                top: "-10px",
                left: "50%",
                transform: "translateX(-50%)",
                backgroundColor: theme.palette.background.paper,
                padding: "0 8px",
              }}
            >
              OR CONTINUE WITH
            </Typography>
          </AuthDivider>

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <SocialButton
                fullWidth
                variant="outlined"
                startIcon={<AccountBalanceWallet />}
                onClick={() => console.log("Connect wallet")}
                disabled={loading}
              >
                Connect Wallet
              </SocialButton>
            </Grid>
          </Grid>
        </AuthPaper>
      </motion.div>
    </AuthContainer>
  );
};

export default Register;
