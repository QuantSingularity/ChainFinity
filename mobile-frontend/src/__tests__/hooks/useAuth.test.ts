import { renderHook, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import React from "react";
import { AppProvider } from "@/context/AppContext";
import { useAuth } from "@/hooks/useAuth";
import * as apiModule from "@/services/api";

jest.mock("@/services/api");

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(AppProvider, null, children);

describe("useAuth hook", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("exposes updatePassword function", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(typeof result.current.updatePassword).toBe("function");
  });

  it("returns loading false initially (after init)", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await act(async () => {});
    expect(result.current.loading).toBe(false);
  });

  it("returns null error initially", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await act(async () => {});
    expect(result.current.error).toBeNull();
  });

  it("returns true on successful password update", async () => {
    const mockAuthAPI = apiModule.authAPI as jest.Mocked<
      typeof apiModule.authAPI
    >;
    (mockAuthAPI.updatePassword as jest.Mock).mockResolvedValue({ data: {} });
    const { result } = renderHook(() => useAuth(), { wrapper });
    let ok = false;
    await act(async () => {
      ok = await result.current.updatePassword({
        currentPassword: "old123",
        newPassword: "new12345",
      });
    });
    expect(ok).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("sets error on failed password update", async () => {
    const mockAuthAPI = apiModule.authAPI as jest.Mocked<
      typeof apiModule.authAPI
    >;
    (mockAuthAPI.updatePassword as jest.Mock).mockRejectedValue({
      response: { status: 400, data: { detail: "Incorrect current password" } },
    });
    const { result } = renderHook(() => useAuth(), { wrapper });
    let ok = true;
    await act(async () => {
      ok = await result.current.updatePassword({
        currentPassword: "wrong",
        newPassword: "new12345",
      });
    });
    expect(ok).toBe(false);
    expect(result.current.error).toBe("Incorrect current password");
  });
});
