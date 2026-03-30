import { act, renderHook, waitFor } from "@testing-library/react";
import type React from "react";
import { AppProvider, useApp } from "@/context/AppContext";
import * as apiModule from "@/services/api";

jest.mock("@/services/api");

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AppProvider>{children}</AppProvider>
);

describe("AppContext", () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("provides initial state", () => {
    const { result } = renderHook(() => useApp(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.loading).toBe(false);
  });

  it("toggles dark mode", () => {
    const { result } = renderHook(() => useApp(), { wrapper });

    act(() => {
      result.current.actions.toggleTheme();
    });

    expect(result.current.darkMode).toBe(true);
  });

  it("handles successful login", async () => {
    const mockAuthAPI = apiModule.authAPI as jest.Mocked<
      typeof apiModule.authAPI
    >;
    mockAuthAPI.login.mockResolvedValue({
      data: { access_token: "mock-token" },
    } as any);
    mockAuthAPI.getCurrentUser.mockResolvedValue({
      data: { id: "1", username: "testuser", email: "test@example.com" },
    } as any);

    const { result } = renderHook(() => useApp(), { wrapper });

    let loginResult: boolean = false;
    await act(async () => {
      loginResult = await result.current.actions.login({
        email: "test@example.com",
        password: "password123",
      });
    });

    expect(loginResult).toBe(true);
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  it("handles logout", () => {
    const { result } = renderHook(() => useApp(), { wrapper });

    act(() => {
      result.current.actions.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
