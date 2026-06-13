"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"
import { getToken, setToken, clearToken } from "@/lib/api/client"
import { login as apiLogin, register as apiRegister, getMe } from "@/lib/api/auth"
import type { User, LoginRequest, RegisterRequest } from "@/types/user"

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
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
    if (!getToken()) {
      setIsLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    const { access_token } = await apiLogin(credentials)
    setToken(access_token)
    setUser(await getMe())
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    const { access_token } = await apiRegister(data)
    setToken(access_token)
    setUser(await getMe())
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
