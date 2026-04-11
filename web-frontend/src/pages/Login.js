import {
  AccountBalanceWallet,
  Email,
  Lock,
  Visibility,
  VisibilityOff,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Container,
  Divider,
  FormControlLabel,
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

const Login = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { login, error, loading, clearError } = useApp();

  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [formError, setFormError] = useState("");

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous errors
    clearError();
    setFormError("");

    if (!email || !password) {
      setFormError("Please enter both email and password");
      return;
    }

    try {
      const success = await login({ email, password });

      if (success) {
        // Redirect to dashboard on success
        navigate("/dashboard");
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
            Welcome Back
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sign in to access your ChainFinity dashboard
          </Typography>
        </Box>

        <AuthPaper elevation={3}>
          {(error || formError) && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {formError ||
                error?.message ||
                "Authentication failed. Please try again."}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email Address"
              variant="outlined"
              margin="normal"
              required
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

            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mt: 1,
                mb: 2,
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    color="primary"
                    disabled={loading}
                  />
                }
                label="Remember me"
              />
              <Link
                component={RouterLink}
                to="/forgot-password"
                variant="body2"
                color="primary"
              >
                Forgot password?
              </Link>
            </Box>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              sx={{ py: 1.5, mb: 2 }}
              disabled={loading}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Sign In"
              )}
            </Button>

            <Box sx={{ textAlign: "center", mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{" "}
                <Link
                  component={RouterLink}
                  to="/register"
                  fontWeight={600}
                  color="primary"
                >
                  Sign Up
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
            <Grid item xs={12} sm={6}>
              <SocialButton
                fullWidth
                variant="outlined"
                startIcon={<AccountBalanceWallet />}
                onClick={() =>
                  window.open(
                    "https://metamask.io",
                    "_blank",
                    "noopener,noreferrer",
                  )
                }
                disabled={loading}
              >
                Connect Wallet
              </SocialButton>
            </Grid>
            <Grid item xs={12} sm={6}>
              <SocialButton
                fullWidth
                variant="outlined"
                onClick={() => {
                  setEmail("guest@chainfinity.io");
                  setPassword("guest1234");
                }}
                disabled={loading}
              >
                Guest Access
              </SocialButton>
            </Grid>
          </Grid>
        </AuthPaper>
      </motion.div>
    </AuthContainer>
  );
};

export default Login;
