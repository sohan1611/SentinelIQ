import { describe, expect, it } from "vitest"
import { resolveApiBaseUrl } from "./client"

describe("resolveApiBaseUrl", () => {
  it("returns a clean URL unchanged", () => {
    expect(resolveApiBaseUrl("https://api.example.com")).toBe("https://api.example.com")
  })

  it("removes a leading BOM so the URL remains absolute", () => {
    const result = resolveApiBaseUrl("\uFEFFhttps://api.example.com")

    expect(result).toBe("https://api.example.com")
    expect(result).not.toContain("\uFEFF")
    expect(result.startsWith("https://")).toBe(true)
  })

  it("strips leading and trailing ordinary whitespace", () => {
    expect(resolveApiBaseUrl(" \nhttps://api.example.com\t ")).toBe("https://api.example.com")
  })

  it("strips surrounding single and double quotes", () => {
    expect(resolveApiBaseUrl('"https://api.example.com"')).toBe("https://api.example.com")
    expect(resolveApiBaseUrl("'https://api.example.com'")).toBe("https://api.example.com")
  })

  it("strips trailing slashes", () => {
    expect(resolveApiBaseUrl("https://api.example.com/")).toBe("https://api.example.com")
  })

  it("falls back for undefined and empty values", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("http://localhost:8000")
    expect(resolveApiBaseUrl(" \t\n ")).toBe("http://localhost:8000")
  })

  it("strips other zero-width characters", () => {
    expect(resolveApiBaseUrl("\u200Bhttps://api.example.com\u200B")).toBe("https://api.example.com")
  })
})
