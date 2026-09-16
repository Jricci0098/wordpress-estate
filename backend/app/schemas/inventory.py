"""Versioned inventory ingestion schema (inventory/v1).

Only ``inventory/v1`` is accepted. Any other ``schema_version`` value is
rejected so that future schema changes cannot be silently misinterpreted.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

SUPPORTED_SCHEMA_VERSION = "inventory/v1"

PluginKind = Literal["plugin", "mu-plugin", "dropin"]
PluginOrigin = Literal["wordpress_org", "commercial", "custom", "unknown"]
PluginRuntimeStatus = Literal["active", "inactive", "unknown"]
PluginUpdateStatus = Literal["current", "behind", "unknown"]
PluginApprovalStatus = Literal["approved", "unapproved", "unknown"]


class HostInfo(BaseModel):
    hostname: str
    os_info: str | None = None


class PluginEntry(BaseModel):
    slug: str
    name: str
    version: str | None = None
    path: str
    kind: PluginKind = "plugin"
    origin: PluginOrigin
    status: PluginRuntimeStatus = "unknown"
    update_status: PluginUpdateStatus = "unknown"
    approval_status: PluginApprovalStatus = "unknown"
    author: str | None = None
    plugin_uri: str | None = None

    @model_validator(mode="after")
    def _no_source_never_current(self) -> "PluginEntry":
        """Commercial/custom/unknown-origin plugins can never be reported "current".

        There is no trusted upstream source to compare the installed version
        against, so the only honest states are "behind" (if a newer version
        was explicitly observed some other way) or "unknown".
        """
        if self.origin != "wordpress_org" and self.update_status == "current":
            raise ValueError(
                "plugins without a wordpress_org source cannot have update_status='current'"
            )
        return self


class SiteInventory(BaseModel):
    site_name: str
    site_url: str
    wp_version: str | None = None
    plugins: list[PluginEntry] = Field(default_factory=list)


class InventoryPayload(BaseModel):
    schema_version: Literal["inventory/v1"]
    agent_id: str
    request_id: str
    timestamp: datetime
    host: HostInfo
    sites: list[SiteInventory] = Field(min_length=1)
