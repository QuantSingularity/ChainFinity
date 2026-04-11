"use client";
import { useState } from "react";
import { Eye, EyeOff, Lock, Save, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "../../hooks/useAuth";

const SettingsPage = () => {
  const { updatePassword, loading, error: authError } = useAuth();
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
    setError(null);
    setSuccess(false);
  };

  const handlePasswordSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (passwordData.newPassword.length < 8) {
      setError("New password must be at least 8 characters long");
      return;
    }
    try {
      const ok = await updatePassword({
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword,
      });
      if (ok) {
        setSuccess(true);
        setPasswordData({
          currentPassword: "",
          newPassword: "",
          confirmPassword: "",
        });
      }
    } catch (err: any) {
      setError(err?.message || "Failed to update password");
    }
  };

  const toggleShow = (field: "current" | "new" | "confirm") =>
    setShowPasswords((prev) => ({ ...prev, [field]: !prev[field] }));

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
          Settings
        </h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Manage your account preferences and security.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-indigo-500" />
            Change Password
          </CardTitle>
          <CardDescription>
            Update your password to keep your account secure.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {(error || authError) && (
            <div className="mb-4 rounded-md bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
              {error || authError}
            </div>
          )}
          {success && (
            <div className="mb-4 rounded-md bg-green-500/10 border border-green-500/30 px-4 py-3 text-sm text-green-600 dark:text-green-400">
              Password updated successfully!
            </div>
          )}
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {(["current", "new", "confirm"] as const).map((field) => (
              <div key={field} className="space-y-2">
                <Label htmlFor={`${field}Password`}>
                  {field === "current"
                    ? "Current Password"
                    : field === "new"
                      ? "New Password"
                      : "Confirm New Password"}
                </Label>
                <div className="relative">
                  <Input
                    id={`${field}Password`}
                    name={`${field}Password`}
                    type={showPasswords[field] ? "text" : "password"}
                    required
                    value={
                      passwordData[
                        `${field}Password` as keyof typeof passwordData
                      ]
                    }
                    onChange={handlePasswordChange}
                    disabled={loading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShow(field)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label="Toggle password visibility"
                  >
                    {showPasswords[field] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-700 hover:to-cyan-700 text-white"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Updating…
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Save className="h-4 w-4" />
                  Update Password
                </span>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-cyan-500" />
            Notification Preferences
          </CardTitle>
          <CardDescription>
            Choose how you want to be notified about activity.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(
            [
              {
                key: "email" as const,
                label: "Email Notifications",
                desc: "Receive updates and alerts via email.",
              },
              {
                key: "push" as const,
                label: "Push Notifications",
                desc: "Get browser push notifications.",
              },
              {
                key: "sms" as const,
                label: "SMS Notifications",
                desc: "Receive SMS alerts for critical events.",
              },
            ] as const
          ).map((item, idx, arr) => (
            <div key={item.key}>
              <div className="flex items-center justify-between py-1">
                <div>
                  <p className="text-sm font-medium leading-none">
                    {item.label}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {item.desc}
                  </p>
                </div>
                <Switch
                  checked={notifications[item.key]}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, [item.key]: checked })
                  }
                />
              </div>
              {idx < arr.length - 1 && <Separator className="mt-3" />}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
