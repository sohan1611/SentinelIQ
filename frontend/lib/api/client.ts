import { ApiError } from "@/types/api"

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

function cleanValidationMessage(msg: string): string {
  return msg
    .split("; ")
    .map(s => {
      const m = s.match(/^body(?:\.\w+)?:\s*(.+)$/)
      const cleaned = (m ? m[1] : s).trim()
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
    })
    .filter(Boolean)
    .join(". ")
}

function extractError(body: any): { message?: string; code?: string } {
  const detail = body?.detail ?? body?.error
  if (typeof detail === "string") return { message: detail }
  if (detail && typeof detail === "object") {
    const inner = detail.error ?? detail
    let message: string | undefined = inner.message
    if (inner.code === "VALIDATION_ERROR" && message) {
      message = cleanValidationMessage(message)
    }
    return { message, code: inner.code }
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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: requestBody,
    credentials: "include",
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
