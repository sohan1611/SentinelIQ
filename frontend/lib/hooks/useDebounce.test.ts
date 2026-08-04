import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useDebounce } from "./useDebounce"

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("initial", 300))
    expect(result.current).toBe("initial")
  })

  it("does not update the value before the delay elapses", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: "a" },
    })

    rerender({ value: "b" })

    act(() => {
      vi.advanceTimersByTime(299)
    })

    expect(result.current).toBe("a")
  })

  it("updates the value once the delay elapses", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: "a" },
    })

    rerender({ value: "b" })

    act(() => {
      vi.advanceTimersByTime(300)
    })

    expect(result.current).toBe("b")
  })

  it("resets the timer on rapid successive changes (only the last value wins)", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: "a" },
    })

    rerender({ value: "b" })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    // Still within the delay window -- a new change should restart the timer.
    rerender({ value: "c" })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    // 400ms since "b" was set, but only 200ms since "c" -- "b" should never surface.
    expect(result.current).toBe("a")

    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current).toBe("c")
  })

  it("uses the default 300ms delay when none is provided", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value), {
      initialProps: { value: "a" },
    })

    rerender({ value: "b" })

    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(result.current).toBe("a")

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current).toBe("b")
  })

  it("clears the pending timer on unmount without throwing", () => {
    const { rerender, unmount } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: "a" },
    })

    rerender({ value: "b" })
    expect(() => unmount()).not.toThrow()
  })
})
