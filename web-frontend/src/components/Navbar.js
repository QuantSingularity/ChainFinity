import {
  AppBar,
  Box,
  Button,
  Link,
  Toolbar,
  Typography,
  useTheme,
} from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { formatAddress } from "../utils/helpers";

function Navbar() {
  const _theme = useTheme();
  const location = useLocation();
  const { state, actions } = useApp();
  const { wallet, user } = state;

  const navItems = [
    { label: "Home", path: "/" },
    { label: "Dashboard", path: "/dashboard" },
  ];

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          sx={{
            flexGrow: 1,
            textDecoration: "none",
            color: "inherit",
            fontWeight: "bold",
          }}
        >
          ChainFinity
        </Typography>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              component={RouterLink}
              to={item.path}
              sx={{
                color:
                  location.pathname === item.path ? "primary.main" : "inherit",
                textDecoration: "none",
                "&:hover": {
                  color: "primary.main",
                },
              }}
            >
              {item.label}
            </Link>
          ))}

          {wallet.isConnected ? (
            <Button
              variant="contained"
              color="primary"
              onClick={actions.disconnectWallet}
            >
              {formatAddress(wallet.address)}
            </Button>
          ) : (
            <Button
              variant="contained"
              color="primary"
              onClick={actions.connectWallet}
            >
              Connect Wallet
            </Button>
          )}

          {user ? (
            <Button variant="outlined" color="inherit" onClick={actions.logout}>
              Logout
            </Button>
          ) : (
            <Button
              component={RouterLink}
              to="/login"
              variant="outlined"
              color="inherit"
            >
              Login
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
