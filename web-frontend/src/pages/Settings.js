import {
  AccountCircle,
  DarkMode,
  Delete,
  Edit,
  Language,
  LightMode,
  Notifications,
  Save,
  Security,
  Visibility,
  VisibilityOff,
  Wallet,
} from "@mui/icons-material";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  Container,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { useState } from "react";
import { useApp } from "../context/AppContext";

const SettingsCard = styled(Card)(({ theme }) => ({
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

const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

const Settings = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const { darkMode, toggleTheme } = useApp();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);
  const [language, setLanguage] = useState("english");
  const [saveSuccess, setSaveSuccess] = useState(null);

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    name: "John Doe",
    email: "john.doe@example.com",
    walletAddress: "0x1234...5678",
    bio: "Blockchain enthusiast and crypto investor since 2017.",
  });

  // Security form state
  const [securityForm, setSecurityForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const handleTabChange = (_event, newValue) => {
    setTabValue(newValue);
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileForm({
      ...profileForm,
      [name]: value,
    });
  };

  const handleSecurityChange = (e) => {
    const { name, value } = e.target;
    setSecurityForm({
      ...securityForm,
      [name]: value,
    });
  };

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setSaveSuccess("profile");
    setTimeout(() => setSaveSuccess(null), 3000);
    // Here you would make an API call to save the profile
  };

  const handleSaveSecurity = (e) => {
    e.preventDefault();
    setSaveSuccess("security");
    setSecurityForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    setTimeout(() => setSaveSuccess(null), 3000);
    // Here you would make an API call to update security settings
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
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={itemVariants}>
            <Box sx={{ mb: 4 }}>
              <Typography variant="h4" component="h1" fontWeight={700}>
                Settings
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Manage your account settings and preferences
              </Typography>
            </Box>
          </motion.div>

          <motion.div variants={itemVariants}>
            <Paper
              sx={{
                borderRadius: theme.shape.borderRadius,
                overflow: "hidden",
                mb: 4,
              }}
            >
              <Collapse in={Boolean(saveSuccess)}>
                <Alert severity="success" sx={{ mb: 2 }}>
                  {saveSuccess === "profile"
                    ? "Profile updated successfully!"
                    : "Security settings saved successfully!"}
                </Alert>
              </Collapse>
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
                <Tab
                  label="Profile"
                  icon={<AccountCircle />}
                  iconPosition="start"
                />
                <Tab
                  label="Security"
                  icon={<Security />}
                  iconPosition="start"
                />
                <Tab
                  label="Notifications"
                  icon={<Notifications />}
                  iconPosition="start"
                />
                <Tab
                  label="Preferences"
                  icon={<Language />}
                  iconPosition="start"
                />
              </Tabs>

              <Box sx={{ p: 3 }}>
                {/* Profile Tab */}
                <TabPanel value={tabValue} index={0}>
                  <form onSubmit={handleSaveProfile}>
                    <Grid container spacing={4}>
                      <Grid item xs={12} md={4}>
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                          }}
                        >
                          <Avatar
                            sx={{
                              width: 120,
                              height: 120,
                              mb: 2,
                              bgcolor: theme.palette.primary.main,
                            }}
                          >
                            <Typography variant="h3">
                              {profileForm.name.charAt(0)}
                            </Typography>
                          </Avatar>
                          <Button
                            variant="outlined"
                            startIcon={<Edit />}
                            sx={{ mb: 3 }}
                          >
                            Change Avatar
                          </Button>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            textAlign="center"
                          >
                            Recommended image size: 200x200px. Max file size:
                            5MB.
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={12} md={8}>
                        <Grid container spacing={3}>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Full Name"
                              name="name"
                              value={profileForm.name}
                              onChange={handleProfileChange}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Email Address"
                              name="email"
                              type="email"
                              value={profileForm.email}
                              onChange={handleProfileChange}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Wallet Address"
                              name="walletAddress"
                              value={profileForm.walletAddress}
                              onChange={handleProfileChange}
                              InputProps={{
                                startAdornment: (
                                  <Box component="span" sx={{ mr: 1 }}>
                                    <Wallet fontSize="small" color="action" />
                                  </Box>
                                ),
                                readOnly: true,
                              }}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Bio"
                              name="bio"
                              value={profileForm.bio}
                              onChange={handleProfileChange}
                              multiline
                              rows={4}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <Box
                              sx={{
                                display: "flex",
                                justifyContent: "flex-end",
                                gap: 2,
                              }}
                            >
                              <Button variant="outlined" color="inherit">
                                Cancel
                              </Button>
                              <Button
                                type="submit"
                                variant="contained"
                                color="primary"
                                startIcon={<Save />}
                              >
                                Save Changes
                              </Button>
                            </Box>
                          </Grid>
                        </Grid>
                      </Grid>
                    </Grid>
                  </form>
                </TabPanel>

                {/* Security Tab */}
                <TabPanel value={tabValue} index={1}>
                  <form onSubmit={handleSaveSecurity}>
                    <Grid container spacing={4}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="h6" fontWeight={600} gutterBottom>
                          Change Password
                        </Typography>
                        <Grid container spacing={3}>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Current Password"
                              name="currentPassword"
                              type={showPassword ? "text" : "password"}
                              value={securityForm.currentPassword}
                              onChange={handleSecurityChange}
                              InputProps={{
                                endAdornment: (
                                  <IconButton
                                    onClick={handleTogglePassword}
                                    edge="end"
                                  >
                                    {showPassword ? (
                                      <VisibilityOff />
                                    ) : (
                                      <Visibility />
                                    )}
                                  </IconButton>
                                ),
                              }}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="New Password"
                              name="newPassword"
                              type={showPassword ? "text" : "password"}
                              value={securityForm.newPassword}
                              onChange={handleSecurityChange}
                              InputProps={{
                                endAdornment: (
                                  <IconButton
                                    onClick={handleTogglePassword}
                                    edge="end"
                                  >
                                    {showPassword ? (
                                      <VisibilityOff />
                                    ) : (
                                      <Visibility />
                                    )}
                                  </IconButton>
                                ),
                              }}
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Confirm New Password"
                              name="confirmPassword"
                              type={showPassword ? "text" : "password"}
                              value={securityForm.confirmPassword}
                              onChange={handleSecurityChange}
                              InputProps={{
                                endAdornment: (
                                  <IconButton
                                    onClick={handleTogglePassword}
                                    edge="end"
                                  >
                                    {showPassword ? (
                                      <VisibilityOff />
                                    ) : (
                                      <Visibility />
                                    )}
                                  </IconButton>
                                ),
                              }}
                            />
                          </Grid>
                        </Grid>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <Typography variant="h6" fontWeight={600} gutterBottom>
                          Two-Factor Authentication
                        </Typography>
                        <SettingsCard sx={{ mb: 3 }}>
                          <CardContent>
                            <Box
                              sx={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <Box>
                                <Typography
                                  variant="subtitle1"
                                  fontWeight={600}
                                >
                                  Two-Factor Authentication
                                </Typography>
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  Add an extra layer of security to your account
                                </Typography>
                              </Box>
                              <Switch
                                checked={twoFactorAuth}
                                onChange={(e) =>
                                  setTwoFactorAuth(e.target.checked)
                                }
                                color="primary"
                              />
                            </Box>
                          </CardContent>
                        </SettingsCard>

                        <Typography variant="h6" fontWeight={600} gutterBottom>
                          Connected Wallets
                        </Typography>
                        <SettingsCard>
                          <CardContent>
                            <Box
                              sx={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                }}
                              >
                                <Avatar
                                  sx={{
                                    bgcolor: theme.palette.primary.main,
                                    mr: 2,
                                  }}
                                >
                                  <Wallet />
                                </Avatar>
                                <Box>
                                  <Typography
                                    variant="subtitle1"
                                    fontWeight={600}
                                  >
                                    Ethereum Wallet
                                  </Typography>
                                  <Typography
                                    variant="body2"
                                    color="text.secondary"
                                  >
                                    {profileForm.walletAddress}
                                  </Typography>
                                </Box>
                              </Box>
                              <Chip
                                label="Primary"
                                color="primary"
                                size="small"
                              />
                            </Box>
                          </CardContent>
                        </SettingsCard>
                      </Grid>

                      <Grid item xs={12}>
                        <Divider sx={{ my: 2 }} />
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                          }}
                        >
                          <Box>
                            <Typography
                              variant="h6"
                              color="error.main"
                              fontWeight={600}
                            >
                              Danger Zone
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Once you delete your account, there is no going
                              back. Please be certain.
                            </Typography>
                          </Box>
                          <Button
                            variant="outlined"
                            color="error"
                            startIcon={<Delete />}
                          >
                            Delete Account
                          </Button>
                        </Box>
                      </Grid>

                      <Grid item xs={12}>
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "flex-end",
                            gap: 2,
                          }}
                        >
                          <Button variant="outlined" color="inherit">
                            Cancel
                          </Button>
                          <Button
                            type="submit"
                            variant="contained"
                            color="primary"
                            startIcon={<Save />}
                          >
                            Save Changes
                          </Button>
                        </Box>
                      </Grid>
                    </Grid>
                  </form>
                </TabPanel>

                {/* Notifications Tab */}
                <TabPanel value={tabValue} index={2}>
                  <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Email Notifications
                      </Typography>
                      <Card
                        sx={{
                          mb: 3,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <List disablePadding>
                          <ListItem divider>
                            <ListItemText
                              primary="Transaction Updates"
                              secondary="Receive emails for transaction confirmations"
                            />
                            <Switch
                              edge="end"
                              checked={emailNotifications}
                              onChange={(e) =>
                                setEmailNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem divider>
                            <ListItemText
                              primary="Portfolio Alerts"
                              secondary="Get notified about significant changes in your portfolio"
                            />
                            <Switch
                              edge="end"
                              checked={emailNotifications}
                              onChange={(e) =>
                                setEmailNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem divider>
                            <ListItemText
                              primary="Security Alerts"
                              secondary="Receive emails about security-related events"
                            />
                            <Switch
                              edge="end"
                              checked={emailNotifications}
                              onChange={(e) =>
                                setEmailNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Marketing & Newsletter"
                              secondary="Stay updated with our latest features and announcements"
                            />
                            <Switch edge="end" checked={false} />
                          </ListItem>
                        </List>
                      </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Push Notifications
                      </Typography>
                      <Card
                        sx={{
                          mb: 3,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <List disablePadding>
                          <ListItem divider>
                            <ListItemText
                              primary="Transaction Updates"
                              secondary="Receive push notifications for transaction confirmations"
                            />
                            <Switch
                              edge="end"
                              checked={pushNotifications}
                              onChange={(e) =>
                                setPushNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem divider>
                            <ListItemText
                              primary="Portfolio Alerts"
                              secondary="Get notified about significant changes in your portfolio"
                            />
                            <Switch
                              edge="end"
                              checked={pushNotifications}
                              onChange={(e) =>
                                setPushNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem divider>
                            <ListItemText
                              primary="Security Alerts"
                              secondary="Receive push notifications about security-related events"
                            />
                            <Switch
                              edge="end"
                              checked={pushNotifications}
                              onChange={(e) =>
                                setPushNotifications(e.target.checked)
                              }
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Price Alerts"
                              secondary="Get notified when assets reach your target price"
                            />
                            <Switch edge="end" checked={true} />
                          </ListItem>
                        </List>
                      </Card>
                    </Grid>

                    <Grid item xs={12}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "flex-end",
                          gap: 2,
                        }}
                      >
                        <Button variant="outlined" color="inherit">
                          Cancel
                        </Button>
                        <Button
                          variant="contained"
                          color="primary"
                          startIcon={<Save />}
                        >
                          Save Changes
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </TabPanel>

                {/* Preferences Tab */}
                <TabPanel value={tabValue} index={3}>
                  <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Appearance
                      </Typography>
                      <Card
                        sx={{
                          mb: 3,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <CardContent>
                          <Box
                            sx={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                            }}
                          >
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                              }}
                            >
                              {darkMode ? (
                                <DarkMode sx={{ mr: 2 }} />
                              ) : (
                                <LightMode sx={{ mr: 2 }} />
                              )}
                              <Box>
                                <Typography
                                  variant="subtitle1"
                                  fontWeight={600}
                                >
                                  {darkMode ? "Dark Mode" : "Light Mode"}
                                </Typography>
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  {darkMode
                                    ? "Switch to light mode"
                                    : "Switch to dark mode"}
                                </Typography>
                              </Box>
                            </Box>
                            <Switch
                              checked={darkMode}
                              onChange={toggleTheme}
                              color="primary"
                            />
                          </Box>
                        </CardContent>
                      </Card>

                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Language
                      </Typography>
                      <Card
                        sx={{
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <CardContent>
                          <TextField
                            select
                            fullWidth
                            label="Language"
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                            SelectProps={{
                              native: true,
                            }}
                          >
                            <option value="english">English</option>
                            <option value="spanish">Spanish</option>
                            <option value="french">French</option>
                            <option value="german">German</option>
                            <option value="chinese">Chinese</option>
                            <option value="japanese">Japanese</option>
                          </TextField>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Currency
                      </Typography>
                      <Card
                        sx={{
                          mb: 3,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <CardContent>
                          <TextField
                            select
                            fullWidth
                            label="Default Currency"
                            value="usd"
                            SelectProps={{
                              native: true,
                            }}
                          >
                            <option value="usd">USD ($)</option>
                            <option value="eur">EUR (€)</option>
                            <option value="gbp">GBP (£)</option>
                            <option value="jpy">JPY (¥)</option>
                            <option value="cny">CNY (¥)</option>
                            <option value="btc">BTC (₿)</option>
                            <option value="eth">ETH (Ξ)</option>
                          </TextField>
                        </CardContent>
                      </Card>

                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Time Zone
                      </Typography>
                      <Card
                        sx={{
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <CardContent>
                          <TextField
                            select
                            fullWidth
                            label="Time Zone"
                            value="utc"
                            SelectProps={{
                              native: true,
                            }}
                          >
                            <option value="utc">
                              UTC (Coordinated Universal Time)
                            </option>
                            <option value="est">
                              EST (Eastern Standard Time)
                            </option>
                            <option value="cst">
                              CST (Central Standard Time)
                            </option>
                            <option value="mst">
                              MST (Mountain Standard Time)
                            </option>
                            <option value="pst">
                              PST (Pacific Standard Time)
                            </option>
                            <option value="gmt">
                              GMT (Greenwich Mean Time)
                            </option>
                            <option value="cet">
                              CET (Central European Time)
                            </option>
                          </TextField>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={12}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "flex-end",
                          gap: 2,
                        }}
                      >
                        <Button variant="outlined" color="inherit">
                          Cancel
                        </Button>
                        <Button
                          variant="contained"
                          color="primary"
                          startIcon={<Save />}
                        >
                          Save Changes
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </TabPanel>
              </Box>
            </Paper>
          </motion.div>
        </motion.div>
      </Container>
    </Box>
  );
};

export default Settings;
