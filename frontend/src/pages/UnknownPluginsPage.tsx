import { fetchUnknownPlugins } from "../api/client";
import { PluginsTable } from "./PluginsTable";

export function UnknownPluginsPage() {
  return (
    <PluginsTable
      title="Unknown Plugins"
      fetcher={() => fetchUnknownPlugins(1, 100)}
      emptyMessage="No unknown-origin plugins reported. That doesn't mean everything is safe or approved — it means nothing unidentifiable was seen."
    />
  );
}
