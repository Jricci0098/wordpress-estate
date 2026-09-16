import { useState } from "react";

import { exportPluginsCsvUrl } from "./api/client";
import { OverviewPage } from "./pages/OverviewPage";
import { PluginsPage } from "./pages/PluginsPage";
import { SitesPage } from "./pages/SitesPage";
import { UnknownPluginsPage } from "./pages/UnknownPluginsPage";

type Tab = "overview" | "sites" | "plugins" | "unknown";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "sites", label: "Sites" },
  { key: "plugins", label: "Plugins" },
  { key: "unknown", label: "Unknown Plugins" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="app">
      <header>
        <h1>WordPress Estate</h1>
        <nav>
          {TABS.map((t) => (
            <button
              key={t.key}
              className={t.key === tab ? "active" : ""}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
          <a className="export-link" href={exportPluginsCsvUrl()}>
            Export CSV
          </a>
        </nav>
      </header>
      <main>
        {tab === "overview" && <OverviewPage />}
        {tab === "sites" && <SitesPage />}
        {tab === "plugins" && <PluginsPage />}
        {tab === "unknown" && <UnknownPluginsPage />}
      </main>
    </div>
  );
}
