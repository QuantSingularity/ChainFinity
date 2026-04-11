"use client";
import { useCallback, useState } from "react";
import { useApp } from "../context/AppContext";
import { authAPI, handleApiError } from "../services/api";

export interface PasswordUpdateData {
  currentPassword: string;
  newPassword: string;
}

export const useAuth = () => {
  const { actions, loading: globalLoading, error: globalError } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updatePassword = useCallback(
    async (data: PasswordUpdateData): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        await authAPI.updatePassword(data);
        setLoading(false);
        return true;
      } catch (err) {
        const apiError = handleApiError(err);
        setError(apiError.message);
        setLoading(false);
        return false;
      }
    },
    [],
  );

  const clearAuthError = useCallback(() => {
    setError(null);
  }, []);

  return {
    updatePassword,
    loading: loading || globalLoading,
    error: error || (globalError?.message ?? null),
    clearAuthError,
    login: actions.login,
    logout: actions.logout,
    register: actions.register,
  };
};

export default useAuth;
