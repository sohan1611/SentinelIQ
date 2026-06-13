import { ApiError } from "@/types/api"

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`

const TOKEN_STORAGE_KEY = "sentineliq_token"

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

function extractError(body: any): { message?: string; code?: string } {
  const detail = body?.detail ?? body?.error
  if (typeof detail === "string") return { message: detail }
  if (detail && typeof detail === "object") {
    const inner = detail.error ?? detail
    return { message: inner.message, code: inner.code }
  }
  return {}
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options

  const requestHeaders = new Headers(headers)
  requestHeaders.set("Accept", "application/json")

  let requestBody: BodyInit | undefined
  if (body !== undefined) {
    if (body instanceof URLSearchParams) {
      requestHeaders.set("Content-Type", "application/x-www-form-urlencoded")
      requestBody = body
    } else {
      requestHeaders.set("Content-Type", "application/json")
      requestBody = JSON.stringify(body)
    }
  }

  const token = getToken()
  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: requestBody,
  })

  if (!response.ok) {
    let errorBody: any = null
    try {
      errorBody = await response.json()
    } catch {
      // no JSON error body
    }
    const { message, code } = extractError(errorBody)
    throw new ApiError(message || response.statusText || "Request failed", response.status, code)
  }

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}
