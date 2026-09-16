import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as client from "../src/api/client";
import { SitesPage } from "../src/pages/SitesPage";

describe("SitesPage", () => {
  it("shows a loading state, then renders fetched sites", async () => {
    vi.spyOn(client, "fetchSites").mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 20,
      items: [
        {
          id: "s1",
          name: "wp1",
          url: "http://localhost:8081",
          wp_version: "6.6.2",
          host_name: "demo-host",
          snapshot_count: 2,
          last_seen_at: new Date().toISOString(),
        },
      ],
    });

    render(<SitesPage />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("wp1")).toBeInTheDocument());
    expect(screen.getByText("http://localhost:8081")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    vi.spyOn(client, "fetchSites").mockRejectedValue(new Error("network down"));

    render(<SitesPage />);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("network down");
  });
});
