import { apiRequest } from "./client"
import type { User, LoginRequest, RegisterRequest } from "@/types/user"

export function login(credentials: LoginRequest): Promise<void> {
  const form = new URLSearchParams()
  form.set("username", credentials.email)
  form.set("password", credentials.password)
  return apiRequest<void>("/auth/login", { method: "POST", body: form })
}

export function register(data: RegisterRequest): Promise<void> {
  return apiRequest<void>("/auth/register", { method: "POST", body: data })
}

export function logout(): Promise<void> {
  return apiRequest<void>("/auth/logout", { method: "POST" })
}

export function getMe(): Promise<User> {
  return apiRequest<User>("/auth/me")
}
