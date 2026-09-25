"""Plugin discovery and registration.

Plugins are found two ways:
1. Installed packages that declare an entry point under the
   "redbench.plugins" group (see pyproject.toml) — this is how third
   parties ship a plugin as its own pip-installable package.
2. Manual registration via `register()`, useful for local development
   or dynamically constructed plugins.
"""

from __future__ import annotations

from importlib.metadata import entry_points

from redbench.core.plugin_base import RedTeamPlugin

_ENTRY_POINT_GROUP = "redbench.plugins"


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, type[RedTeamPlugin]] = {}

    def register(self, plugin_cls: type[RedTeamPlugin]) -> None:
        key = plugin_cls.name
        if key in self._plugins and self._plugins[key] is not plugin_cls:
            raise ValueError(f"A plugin named '{key}' is already registered")
        self._plugins[key] = plugin_cls

    def load_entry_points(self) -> None:
        """Discover and register any pip-installed plugins."""
        try:
            eps = entry_points(group=_ENTRY_POINT_GROUP)
        except TypeError:  # Python < 3.10 signature fallback
            eps = entry_points().get(_ENTRY_POINT_GROUP, [])

        for ep in eps:
            plugin_cls = ep.load()
            self.register(plugin_cls)

    def get(self, name: str) -> type[RedTeamPlugin]:
        if name not in self._plugins:
            available = ", ".join(sorted(self._plugins)) or "(none registered)"
            raise KeyError(f"No plugin named '{name}'. Available: {available}")
        return self._plugins[name]

    def list_plugins(self) -> list[type[RedTeamPlugin]]:
        return list(self._plugins.values())


# A process-wide default registry, so callers don't have to wire one
# through manually for simple use cases.
default_registry = PluginRegistry()
