export interface Page<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface Site {
  id: string;
  name: string;
  url: string;
  wp_version: string | null;
  host_name: string | null;
  snapshot_count: number;
  last_seen_at: string;
}

export type PluginKind = "plugin" | "mu-plugin" | "dropin";
export type PluginOrigin = "wordpress_org" | "commercial" | "custom" | "unknown";
export type PluginRuntimeStatus = "active" | "inactive" | "unknown";
export type PluginUpdateStatus = "current" | "behind" | "unknown";
export type PluginApprovalStatus = "approved" | "unapproved" | "unknown";

export interface PluginInstallation {
  id: string;
  site_name: string;
  slug: string;
  name: string;
  version: string | null;
  path: string;
  kind: PluginKind;
  origin: PluginOrigin;
  status: PluginRuntimeStatus;
  update_status: PluginUpdateStatus;
  approval_status: PluginApprovalStatus;
}
