import type { Page, PluginInstallation, Site } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8001";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchSites(page = 1, pageSize = 20): Promise<Page<Site>> {
  return getJson<Page<Site>>(`/api/v1/sites?page=${page}&page_size=${pageSize}`);
}

export function fetchPlugins(page = 1, pageSize = 20): Promise<Page<PluginInstallation>> {
  return getJson<Page<PluginInstallation>>(`/api/v1/plugins?page=${page}&page_size=${pageSize}`);
}

export function fetchUnknownPlugins(
  page = 1,
  pageSize = 20,
): Promise<Page<PluginInstallation>> {
  return getJson<Page<PluginInstallation>>(
    `/api/v1/plugins/unknown?page=${page}&page_size=${pageSize}`,
  );
}

export function exportPluginsCsvUrl(): string {
  return `${API_BASE_URL}/api/v1/export/plugins.csv`;
}
