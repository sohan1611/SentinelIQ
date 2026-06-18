"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"
import { login as apiLogin, register as apiRegister, logout as apiLogout, getMe } from "@/lib/api/auth"
import type { User, LoginRequest, RegisterRequest } from "@/types/user"

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Cookie is sent automatically — just try /auth/me. A 401 means no session.
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    await apiLogin(credentials)
    setUser(await getMe())
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    await apiRegister(data)
    setUser(await getMe())
  }, [])

  const logout = useCallback(async () => {
    setUser(null)
    try { await apiLogout() } catch {}
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
