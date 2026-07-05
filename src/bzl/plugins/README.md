# Plugins (future)

This package defines the *shape* of future plugin extension points — `PluginCommand`, `PluginProvider`, `PluginWidget` in `base.py` — but there is no runtime plugin loader in v0.1. No plugins are discovered, imported, or executed automatically. This exists only so future work (dynamic loading from a `plugins/` directory or installed packages) has an interface to target without redesigning `commands/`, `providers/`, or `ui/`.
