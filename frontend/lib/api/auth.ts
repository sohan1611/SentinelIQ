import { apiRequest } from "./client"
import type { Token, User, LoginRequest, RegisterRequest } from "@/types/user"

export function login(credentials: LoginRequest): Promise<Token> {
  const form = new URLSearchParams()
  form.set("username", credentials.email)
  form.set("password", credentials.password)
  return apiRequest<Token>("/auth/login", { method: "POST", body: form })
}

export function register(data: RegisterRequest): Promise<Token> {
  return apiRequest<Token>("/auth/register", { method: "POST", body: data })
}

export function getMe(): Promise<User> {
  return apiRequest<User>("/auth/me")
}
