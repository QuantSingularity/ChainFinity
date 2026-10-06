import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import React from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AppProvider } from "../src/context/AppContext";
import { ThemeProvider, useTheme } from "../src/theme/ThemeContext";

function ThemedStack() {
  const { theme, isDark } = useTheme();
  return (
    <>
      <StatusBar style={isDark ? "light" : "dark"} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme.colors.surface },
          headerTintColor: theme.colors.textPrimary,
          headerTitleStyle: { fontWeight: "700" },
          headerShadowVisible: false,
          contentStyle: { backgroundColor: theme.colors.background },
        }}
      >
        <Stack.Screen
          name="index"
          options={{ title: "ChainFinity", headerShown: false }}
        />
        <Stack.Screen name="login" options={{ title: "Sign In" }} />
        <Stack.Screen name="register" options={{ title: "Create Account" }} />
        <Stack.Screen
          name="forgot-password"
          options={{ title: "Reset Password" }}
        />
        <Stack.Screen name="dashboard" options={{ title: "Dashboard" }} />
        <Stack.Screen name="portfolio" options={{ title: "Portfolio" }} />
        <Stack.Screen name="risk" options={{ title: "Risk Intelligence" }} />
        <Stack.Screen name="transactions" options={{ title: "Transactions" }} />
        <Stack.Screen name="governance" options={{ title: "Governance" }} />
        <Stack.Screen name="settings" options={{ title: "Settings" }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AppProvider>
          <ThemedStack />
        </AppProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
