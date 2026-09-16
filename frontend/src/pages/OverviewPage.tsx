import { fetchPlugins, fetchSites, fetchUnknownPlugins } from "../api/client";
import { useApiResource } from "../api/useApiResource";

interface OverviewCounts {
  siteCount: number;
  pluginCount: number;
  unknownCount: number;
}

async function loadOverview(): Promise<OverviewCounts> {
  const [sites, plugins, unknown] = await Promise.all([
    fetchSites(1, 1),
    fetchPlugins(1, 1),
    fetchUnknownPlugins(1, 1),
  ]);
  return { siteCount: sites.total, pluginCount: plugins.total, unknownCount: unknown.total };
}

export function OverviewPage() {
  const { data, loading, error } = useApiResource(loadOverview, []);

  if (loading) return <p>Loading overview…</p>;
  if (error)
    return (
      <p role="alert">
        Failed to load overview: {error}
      </p>
    );
  if (!data) return null;

  return (
    <div>
      <div className="cards">
        <div className="card">
          <h2>{data.siteCount}</h2>
          <p>Sites</p>
        </div>
        <div className="card">
          <h2>{data.pluginCount}</h2>
          <p>Installed plugins (latest snapshot)</p>
        </div>
        <div className="card">
          <h2>{data.unknownCount}</h2>
          <p>Unknown-origin plugins</p>
        </div>
      </div>
      <p className="disclaimer">
        These counts reflect what agents reported and the backend ingested. "Installed" does
        not mean "current", "approved", or "secure" — check the Plugins and Unknown Plugins
        views for the actual update/approval status of each plugin.
      </p>
    </div>
  );
}
