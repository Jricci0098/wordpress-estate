import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useApiResource } from "../src/api/useApiResource";

describe("useApiResource", () => {
  it("starts in a loading state, then resolves with data", async () => {
    const { result } = renderHook(() => useApiResource(() => Promise.resolve({ total: 5 }), []));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ total: 5 });
    expect(result.current.error).toBeNull();
  });

  it("captures an error message when the fetcher rejects", async () => {
    const { result } = renderHook(() =>
      useApiResource(() => Promise.reject(new Error("boom")), []),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe("boom");
    expect(result.current.data).toBeNull();
  });
});
