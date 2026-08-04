"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api-client";
import { getAccessToken, setAccessToken } from "./token-store";
import type { TokenResponse, UserOut } from "@/types/api";

interface AuthContextValue {
  user: UserOut | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<UserOut>;
  register: (email: string, password: string, fullName: string) => Promise<UserOut>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const me = await api.get<UserOut>("/auth/me");
    setUser(me);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (getAccessToken()) {
        try {
          const me = await api.get<UserOut>("/auth/me");
          if (!cancelled) setUser(me);
          if (!cancelled) setIsLoading(false);
          return;
        } catch {
          setAccessToken(null);
        }
      }
      try {
        const data = await api.post<TokenResponse>("/auth/refresh", undefined, { skipAuth: true });
        setAccessToken(data.access_token);
        if (!cancelled) setUser(data.user);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<TokenResponse>("/auth/login", { email, password }, { skipAuth: true });
    setAccessToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    const data = await api.post<TokenResponse>(
      "/auth/register",
      { email, password, full_name: fullName },
      { skipAuth: true },
    );
    setAccessToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // best-effort revoke; clear client state regardless
    }
    setAccessToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
