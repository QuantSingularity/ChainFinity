"use client";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth"; // Assuming a useAuth hook for password change

const SettingsPage = () => {
  const { updatePassword, loading, error: authError } = useAuth(); // Placeholder hook
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: false,
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handlePasswordChange = (e) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
    setError(null);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    try {
      // Placeholder for actual password update logic
      // await updatePassword({
      //     currentPassword: passwordData.currentPassword,
      //     newPassword: passwordData.newPassword,
      // });
      console.log("Password update simulated");
      setSuccess(true);
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (err) {
      setError(err.message || "Failed to update password");
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom>
        Settings
      </Typography>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Change Password
        </Typography>
        {(error || authError) && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error || authError}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Password updated successfully!
          </Alert>
        )}
        <form onSubmit={handlePasswordSubmit}>
          <TextField
            required
            fullWidth
            margin="normal"
            type="password"
            label="Current Password"
            name="currentPassword"
            value={passwordData.currentPassword}
            onChange={handlePasswordChange}
          />
          <TextField
            required
            fullWidth
            margin="normal"
            type="password"
            label="New Password"
            name="newPassword"
            value={passwordData.newPassword}
            onChange={handlePasswordChange}
          />
          <TextField
            required
            fullWidth
            margin="normal"
            type="password"
            label="Confirm New Password"
            name="confirmPassword"
            value={passwordData.confirmPassword}
            onChange={handlePasswordChange}
          />
          <Button
            type="submit"
            variant="contained"
            sx={{ mt: 2 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : "Update Password"}
          </Button>
        </form>
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Notification Preferences
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={notifications.email}
              onChange={(e) =>
                setNotifications({ ...notifications, email: e.target.checked })
              }
            />
          }
          label="Email Notifications"
        />
        <FormControlLabel
          control={
            <Switch
              checked={notifications.push}
              onChange={(e) =>
                setNotifications({ ...notifications, push: e.target.checked })
              }
            />
          }
          label="Push Notifications"
        />
        <FormControlLabel
          control={
            <Switch
              checked={notifications.sms}
              onChange={(e) =>
                setNotifications({ ...notifications, sms: e.target.checked })
              }
            />
          }
          label="SMS Notifications"
        />
      </Box>
    </Box>
  );
};

export default SettingsPage;
