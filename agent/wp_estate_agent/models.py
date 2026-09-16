from dataclasses import dataclass
from typing import Literal

PluginKind = Literal["plugin", "mu-plugin", "dropin"]
PluginOrigin = Literal["wordpress_org", "commercial", "custom", "unknown"]


@dataclass
class DiscoveredPlugin:
    slug: str
    name: str
    version: str | None
    path: str
    kind: PluginKind
    origin: PluginOrigin
    status: Literal["active", "inactive", "unknown"] = "unknown"
    update_status: Literal["current", "behind", "unknown"] = "unknown"
    approval_status: Literal["approved", "unapproved", "unknown"] = "unknown"
