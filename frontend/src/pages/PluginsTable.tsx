import type { Page, PluginInstallation } from "../api/types";
import { useApiResource } from "../api/useApiResource";

interface Props {
  title: string;
  fetcher: () => Promise<Page<PluginInstallation>>;
  emptyMessage: string;
}

export function PluginsTable({ title, fetcher, emptyMessage }: Props) {
  const { data, loading, error } = useApiResource(fetcher, []);

  if (loading) return <p>Loading {title.toLowerCase()}…</p>;
  if (error)
    return (
      <p role="alert">
        Failed to load {title.toLowerCase()}: {error}
      </p>
    );
  if (!data) return null;

  if (data.items.length === 0) {
    return <p>{emptyMessage}</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Site</th>
          <th>Slug</th>
          <th>Name</th>
          <th>Version</th>
          <th>Kind</th>
          <th>Origin</th>
          <th>Status</th>
          <th>Update status</th>
          <th>Approval</th>
        </tr>
      </thead>
      <tbody>
        {data.items.map((plugin) => (
          <tr key={plugin.id}>
            <td>{plugin.site_name}</td>
            <td>{plugin.slug}</td>
            <td>{plugin.name}</td>
            <td>{plugin.version ?? "—"}</td>
            <td>{plugin.kind}</td>
            <td>{plugin.origin}</td>
            <td>{plugin.status}</td>
            <td>{plugin.update_status}</td>
            <td>{plugin.approval_status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
