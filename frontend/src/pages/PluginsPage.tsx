import { fetchPlugins } from "../api/client";
import { PluginsTable } from "./PluginsTable";

export function PluginsPage() {
  return (
    <PluginsTable
      title="Plugins"
      fetcher={() => fetchPlugins(1, 100)}
      emptyMessage="No plugins reported yet. Post some inventory first."
    />
  );
}
