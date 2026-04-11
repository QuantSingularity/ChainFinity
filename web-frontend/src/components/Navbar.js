import {
  AppBar,
  Box,
  Button,
  Chip,
  Link,
  Toolbar,
  Typography,
} from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { formatAddress } from "../utils/helpers";

function Navbar() {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useApp();

  const navItems = [
    { label: "Home", path: "/" },
    { label: "Dashboard", path: "/dashboard" },
    { label: "Transactions", path: "/transactions" },
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
                "&:hover": { color: "primary.main" },
              }}
            >
              {item.label}
            </Link>
          ))}

          {user?.wallet_address && (
            <Chip
              label={formatAddress(user.wallet_address)}
              color="primary"
              size="small"
              variant="outlined"
            />
          )}

          {isAuthenticated ? (
            <Button variant="outlined" color="inherit" onClick={logout}>
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
