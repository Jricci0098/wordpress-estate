import { fetchSites } from "../api/client";
import { useApiResource } from "../api/useApiResource";

export function SitesPage() {
  const { data, loading, error } = useApiResource(() => fetchSites(1, 50), []);

  if (loading) return <p>Loading sites…</p>;
  if (error)
    return (
      <p role="alert">
        Failed to load sites: {error}
      </p>
    );
  if (!data) return null;

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>URL</th>
          <th>WP Version</th>
          <th>Snapshots</th>
          <th>Last seen</th>
        </tr>
      </thead>
      <tbody>
        {data.items.map((site) => (
          <tr key={site.id}>
            <td>{site.name}</td>
            <td>{site.url}</td>
            <td>{site.wp_version ?? "unknown"}</td>
            <td>{site.snapshot_count}</td>
            <td>{new Date(site.last_seen_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
