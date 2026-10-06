import WalletIcon from "@mui/icons-material/AccountBalanceWallet";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import DashboardIcon from "@mui/icons-material/Dashboard";
import GovernanceIcon from "@mui/icons-material/Gavel";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import PersonIcon from "@mui/icons-material/Person";
import PortfolioIcon from "@mui/icons-material/PieChart";
import RiskIcon from "@mui/icons-material/Security";
import SettingsIcon from "@mui/icons-material/Settings";
import SwapIcon from "@mui/icons-material/SwapHoriz";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Switch,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useState } from "react";
import { Link as RouterLink, useNavigate, useLocation } from "react-router-dom";
import { useApp } from "../../context/AppContext";

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  backgroundColor:
    theme.palette.mode === "light"
      ? "rgba(255, 255, 255, 0.85)"
      : "rgba(26, 26, 46, 0.85)",
  backdropFilter: "blur(10px)",
  boxShadow:
    theme.palette.mode === "light"
      ? "0 1px 0 rgba(0,0,0,0.08)"
      : "0 1px 0 rgba(255,255,255,0.06)",
  color: theme.palette.text.primary,
}));

const NavButton = styled(Button)(({ theme, active }) => ({
  marginLeft: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  textTransform: "none",
  fontWeight: 600,
  color: active ? theme.palette.primary.main : theme.palette.text.primary,
  backgroundColor: active
    ? theme.palette.mode === "light"
      ? "rgba(108, 99, 255, 0.08)"
      : "rgba(108, 99, 255, 0.15)"
    : "transparent",
  "&:hover": {
    backgroundColor:
      theme.palette.mode === "light"
        ? "rgba(108, 99, 255, 0.08)"
        : "rgba(108, 99, 255, 0.15)",
  },
}));

const AUTH_NAV_ITEMS = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: <DashboardIcon fontSize="small" />,
  },
  {
    label: "Portfolio",
    to: "/portfolio",
    icon: <PortfolioIcon fontSize="small" />,
  },
  {
    label: "Risk",
    to: "/risk",
    icon: <RiskIcon fontSize="small" />,
  },
  {
    label: "Transactions",
    to: "/transactions",
    icon: <SwapIcon fontSize="small" />,
  },
  {
    label: "Governance",
    to: "/governance",
    icon: <GovernanceIcon fontSize="small" />,
  },
];

const Navbar = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout, darkMode, toggleTheme } = useApp();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate("/");
  };

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  const userInitial = user?.name
    ? user.name[0].toUpperCase()
    : user?.email
      ? user.email[0].toUpperCase()
      : "U";

  return (
    <StyledAppBar position="sticky">
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ py: 0.5 }}>
          {/* Logo */}
          <Box
            component={RouterLink}
            to="/"
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              textDecoration: "none",
              mr: 3,
            }}
          >
            <Box
              sx={{
                width: 32,
                height: 32,
                borderRadius: "8px",
                background: "linear-gradient(45deg, #3a36e0, #6c63ff)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <WalletIcon sx={{ color: "white", fontSize: 18 }} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={800}
              sx={{
                background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                letterSpacing: "-0.5px",
              }}
            >
              ChainFinity
            </Typography>
          </Box>

          {/* Desktop nav */}
          {!isMobile && isAuthenticated && (
            <Box sx={{ display: "flex", alignItems: "center", flex: 1 }}>
              {AUTH_NAV_ITEMS.map((item) => (
                <NavButton
                  key={item.to}
                  component={RouterLink}
                  to={item.to}
                  active={isActive(item.to) ? 1 : 0}
                  startIcon={item.icon}
                >
                  {item.label}
                </NavButton>
              ))}
            </Box>
          )}

          <Box sx={{ flex: 1 }} />

          {/* Theme toggle */}
          <Tooltip
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            <IconButton onClick={toggleTheme} size="small" sx={{ mr: 1 }}>
              {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Auth buttons / Avatar */}
          {isAuthenticated ? (
            <>
              <Tooltip title="Account">
                <IconButton
                  onClick={handleMenuOpen}
                  size="small"
                  aria-label="Account"
                >
                  <Avatar
                    sx={{
                      width: 36,
                      height: 36,
                      bgcolor: "primary.main",
                      fontSize: "0.875rem",
                      fontWeight: 700,
                    }}
                  >
                    {userInitial}
                  </Avatar>
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                PaperProps={{
                  elevation: 3,
                  sx: { mt: 1, minWidth: 180, borderRadius: 2 },
                }}
                transformOrigin={{ horizontal: "right", vertical: "top" }}
                anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              >
                {user && (
                  <Box sx={{ px: 2, py: 1.5 }}>
                    <Typography variant="subtitle2" fontWeight={700} noWrap>
                      {user.name ?? user.email}
                    </Typography>
                    {user.name && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        noWrap
                      >
                        {user.email}
                      </Typography>
                    )}
                  </Box>
                )}
                <Divider />
                <MenuItem
                  onClick={() => {
                    handleMenuClose();
                    navigate("/settings");
                  }}
                  sx={{ gap: 1.5, py: 1.2 }}
                >
                  <SettingsIcon fontSize="small" color="action" /> Settings
                </MenuItem>
                <Divider />
                <MenuItem
                  onClick={handleLogout}
                  sx={{ gap: 1.5, py: 1.2, color: "error.main" }}
                >
                  <LogoutIcon fontSize="small" /> Sign Out
                </MenuItem>
              </Menu>

              {/* Mobile hamburger */}
              {isMobile && (
                <IconButton onClick={() => setDrawerOpen(true)} sx={{ ml: 1 }}>
                  <MenuIcon />
                </IconButton>
              )}
            </>
          ) : (
            <Box sx={{ display: "flex", gap: 1 }}>
              {!isMobile && (
                <Button
                  component={RouterLink}
                  to="/login"
                  variant="outlined"
                  size="small"
                >
                  Sign In
                </Button>
              )}
              <Button
                component={RouterLink}
                to="/register"
                variant="contained"
                size="small"
                sx={{
                  background: "linear-gradient(45deg, #3a36e0, #6c63ff)",
                  color: "#fff",
                }}
              >
                Get Started
              </Button>
              {isMobile && (
                <IconButton
                  onClick={() => setDrawerOpen(true)}
                  sx={{ ml: 0.5 }}
                >
                  <MenuIcon />
                </IconButton>
              )}
            </Box>
          )}
        </Toolbar>
      </Container>

      {/* Mobile drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{ sx: { width: 280, pt: 2 } }}
      >
        <Box sx={{ px: 2, pb: 2 }}>
          <Typography
            variant="h6"
            fontWeight={800}
            sx={{
              background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              mb: 2,
            }}
          >
            ChainFinity
          </Typography>
        </Box>
        <Divider />
        <List sx={{ px: 1, pt: 1 }}>
          {isAuthenticated ? (
            <>
              {AUTH_NAV_ITEMS.map((item) => (
                <ListItem
                  key={item.to}
                  button
                  component={RouterLink}
                  to={item.to}
                  onClick={() => setDrawerOpen(false)}
                  selected={isActive(item.to)}
                  sx={{ borderRadius: 2, mb: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{ fontWeight: 600 }}
                  />
                </ListItem>
              ))}
              <Divider sx={{ my: 1 }} />
              <ListItem
                button
                component={RouterLink}
                to="/settings"
                onClick={() => setDrawerOpen(false)}
                sx={{ borderRadius: 2, mb: 0.5 }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary="Settings"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItem>
              <ListItem
                button
                onClick={() => {
                  setDrawerOpen(false);
                  handleLogout();
                }}
                sx={{ borderRadius: 2, color: "error.main" }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: "error.main" }}>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary="Sign Out"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItem>
            </>
          ) : (
            <>
              <ListItem
                button
                component={RouterLink}
                to="/login"
                onClick={() => setDrawerOpen(false)}
                sx={{ borderRadius: 2, mb: 0.5 }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary="Sign In"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItem>
              <ListItem
                button
                component={RouterLink}
                to="/register"
                onClick={() => setDrawerOpen(false)}
                sx={{ borderRadius: 2 }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <WalletIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary="Get Started"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItem>
            </>
          )}
          <Divider sx={{ my: 1 }} />
          <ListItem sx={{ borderRadius: 2 }}>
            <ListItemIcon sx={{ minWidth: 36 }}>
              {darkMode ? (
                <LightModeIcon fontSize="small" />
              ) : (
                <DarkModeIcon fontSize="small" />
              )}
            </ListItemIcon>
            <ListItemText primary={darkMode ? "Light Mode" : "Dark Mode"} />
            <Switch checked={darkMode} onChange={toggleTheme} size="small" />
          </ListItem>
        </List>
      </Drawer>
    </StyledAppBar>
  );
};

export default Navbar;
