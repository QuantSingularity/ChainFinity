import {
  DarkMode as DarkModeIcon,
  Dashboard as DashboardIcon,
  LightMode as LightModeIcon,
  Logout as LogoutIcon,
  Menu as MenuIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  SwapHoriz as SwapIcon,
  AccountBalanceWallet as WalletIcon,
} from "@mui/icons-material";
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
import { motion } from "framer-motion";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  backgroundColor:
    theme.palette.mode === "light"
      ? "rgba(255, 255, 255, 0.8)"
      : "rgba(30, 30, 30, 0.8)",
  backdropFilter: "blur(8px)",
  boxShadow: theme.shadows[2],
  color: theme.palette.text.primary,
}));

const LogoContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  gap: theme.spacing(1),
}));

const _Logo = styled("img")({
  height: 40,
});

const NavButton = styled(Button)(({ theme }) => ({
  marginLeft: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  textTransform: "none",
  fontWeight: 600,
}));

const MobileNavItem = styled(ListItem)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(1),
}));

const ThemeToggleSwitch = styled(Switch)(({ theme }) => ({
  width: 62,
  height: 34,
  padding: 7,
  "& .MuiSwitch-switchBase": {
    margin: 1,
    padding: 0,
    transform: "translateX(6px)",
    "&.Mui-checked": {
      transform: "translateX(22px)",
      "& .MuiSwitch-thumb:before": {
        backgroundImage: `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="20" width="20" viewBox="0 0 20 20"><path fill="${encodeURIComponent(
          "#fff",
        )}" d="M4.2 2.5l-.7 1.8-1.8.7 1.8.7.7 1.8.6-1.8L6.7 5l-1.9-.7-.6-1.8zm15 8.3a6.7 6.7 0 11-6.6-6.6 5.8 5.8 0 006.6 6.6z"/></svg>')`,
      },
      "& + .MuiSwitch-track": {
        opacity: 1,
        backgroundColor: theme.palette.mode === "dark" ? "#8796A5" : "#aab4be",
      },
    },
  },
  "& .MuiSwitch-thumb": {
    backgroundColor:
      theme.palette.mode === "dark"
        ? theme.palette.primary.main
        : theme.palette.secondary.main,
    width: 32,
    height: 32,
    "&:before": {
      content: "''",
      position: "absolute",
      width: "100%",
      height: "100%",
      left: 0,
      top: 0,
      backgroundRepeat: "no-repeat",
      backgroundPosition: "center",
      backgroundImage: `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="20" width="20" viewBox="0 0 20 20"><path fill="${encodeURIComponent(
        "#fff",
      )}" d="M9.305 1.667V3.75h1.389V1.667h-1.39zm-4.707 1.95l-.982.982L5.09 6.072l.982-.982-1.473-1.473zm10.802 0L13.927 5.09l.982.982 1.473-1.473-.982-.982zM10 5.139a4.872 4.872 0 00-4.862 4.86A4.872 4.872 0 0010 14.862 4.872 4.872 0 0014.86 10 4.872 4.872 0 0010 5.139zm0 1.389A3.462 3.462 0 0113.471 10a3.462 3.462 0 01-3.473 3.472A3.462 3.462 0 016.527 10 3.462 3.462 0 0110 6.528zM1.665 9.305v1.39h2.083v-1.39H1.666zm14.583 0v1.39h2.084v-1.39h-2.084zM5.09 13.928L3.616 15.4l.982.982 1.473-1.473-.982-.982zm9.82 0l-.982.982 1.473 1.473.982-.982-1.473-1.473zM9.305 16.25v2.083h1.389V16.25h-1.39z"/></svg>')`,
    },
  },
  "& .MuiSwitch-track": {
    opacity: 1,
    backgroundColor: theme.palette.mode === "dark" ? "#8796A5" : "#aab4be",
    borderRadius: 20 / 2,
  },
}));

const Navbar = ({ toggleTheme, themeMode }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const [anchorEl, setAnchorEl] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isMenuOpen = Boolean(anchorEl);

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    // Implement logout functionality
    handleMenuClose();
    navigate("/login");
  };

  const menuId = "primary-account-menu";
  const renderMenu = (
    <Menu
      anchorEl={anchorEl}
      id={menuId}
      keepMounted
      open={isMenuOpen}
      onClose={handleMenuClose}
      PaperProps={{
        elevation: 3,
        sx: {
          borderRadius: 2,
          minWidth: 180,
          mt: 1.5,
        },
      }}
    >
      <MenuItem
        onClick={() => {
          handleMenuClose();
          navigate("/profile");
        }}
      >
        <ListItemIcon>
          <PersonIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Profile</ListItemText>
      </MenuItem>
      <MenuItem
        onClick={() => {
          handleMenuClose();
          navigate("/settings");
        }}
      >
        <ListItemIcon>
          <SettingsIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Settings</ListItemText>
      </MenuItem>
      <Divider />
      <MenuItem onClick={handleLogout}>
        <ListItemIcon>
          <LogoutIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Logout</ListItemText>
      </MenuItem>
    </Menu>
  );

  const drawer = (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
        <LogoContainer>
          <Typography
            variant="h5"
            component="div"
            sx={{
              fontWeight: 700,
              background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            ChainFinity
          </Typography>
        </LogoContainer>
      </Box>
      <Divider sx={{ mb: 2 }} />
      <List>
        <MobileNavItem
          button
          component={RouterLink}
          to="/"
          onClick={handleDrawerToggle}
        >
          <ListItemIcon>
            <DashboardIcon color="primary" />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </MobileNavItem>
        <MobileNavItem
          button
          component={RouterLink}
          to="/wallet"
          onClick={handleDrawerToggle}
        >
          <ListItemIcon>
            <WalletIcon color="primary" />
          </ListItemIcon>
          <ListItemText primary="Wallet" />
        </MobileNavItem>
        <MobileNavItem
          button
          component={RouterLink}
          to="/transactions"
          onClick={handleDrawerToggle}
        >
          <ListItemIcon>
            <SwapIcon color="primary" />
          </ListItemIcon>
          <ListItemText primary="Transactions" />
        </MobileNavItem>
      </List>
      <Divider sx={{ my: 2 }} />
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: 2,
        }}
      >
        <Typography variant="body2">
          {themeMode === "dark" ? "Dark Mode" : "Light Mode"}
        </Typography>
        <ThemeToggleSwitch
          checked={themeMode === "dark"}
          onChange={toggleTheme}
          inputProps={{ "aria-label": "toggle theme" }}
        />
      </Box>
    </Box>
  );

  return (
    <>
      <StyledAppBar
        position="sticky"
        component={motion.div}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            {isMobile ? (
              <>
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
                <LogoContainer sx={{ flexGrow: 1, justifyContent: "center" }}>
                  <Typography
                    variant="h6"
                    component={RouterLink}
                    to="/"
                    sx={{
                      fontWeight: 700,
                      textDecoration: "none",
                      color: "inherit",
                      background:
                        "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                    }}
                  >
                    ChainFinity
                  </Typography>
                </LogoContainer>
              </>
            ) : (
              <>
                <LogoContainer sx={{ flexGrow: 0, mr: 2 }}>
                  <Typography
                    variant="h6"
                    component={RouterLink}
                    to="/"
                    sx={{
                      fontWeight: 700,
                      textDecoration: "none",
                      color: "inherit",
                      background:
                        "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                    }}
                  >
                    ChainFinity
                  </Typography>
                </LogoContainer>
                <Box sx={{ flexGrow: 1, display: "flex" }}>
                  <NavButton
                    component={RouterLink}
                    to="/"
                    color="inherit"
                    startIcon={<DashboardIcon />}
                  >
                    Dashboard
                  </NavButton>
                  <NavButton
                    component={RouterLink}
                    to="/wallet"
                    color="inherit"
                    startIcon={<WalletIcon />}
                  >
                    Wallet
                  </NavButton>
                  <NavButton
                    component={RouterLink}
                    to="/transactions"
                    color="inherit"
                    startIcon={<SwapIcon />}
                  >
                    Transactions
                  </NavButton>
                </Box>
              </>
            )}

            <Box sx={{ display: "flex", alignItems: "center" }}>
              <Tooltip
                title={
                  themeMode === "dark"
                    ? "Switch to Light Mode"
                    : "Switch to Dark Mode"
                }
              >
                <IconButton onClick={toggleTheme} color="inherit">
                  {themeMode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>

              <Tooltip title="Account">
                <IconButton
                  edge="end"
                  aria-label="account of current user"
                  aria-controls={menuId}
                  aria-haspopup="true"
                  onClick={handleProfileMenuOpen}
                  color="inherit"
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: theme.palette.primary.main,
                    }}
                  >
                    <PersonIcon />
                  </Avatar>
                </IconButton>
              </Tooltip>
            </Box>
          </Toolbar>
        </Container>
      </StyledAppBar>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { boxSizing: "border-box", width: 280 },
        }}
      >
        {drawer}
      </Drawer>

      {renderMenu}
    </>
  );
};

export default Navbar;
