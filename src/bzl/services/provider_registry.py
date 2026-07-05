import logging

from bzl.providers.base import AIProvider

logger = logging.getLogger(__name__)


class ProviderNotFoundError(Exception):
    pass


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> AIProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderNotFoundError(f"no provider named {name!r}") from exc

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def default_provider(self, preferred: str | None = None) -> AIProvider:
        if not self._providers:
            raise ProviderNotFoundError("no providers registered")
        if preferred and preferred in self._providers:
            return self._providers[preferred]
        if preferred:
            logger.warning("preferred provider %r not found, falling back", preferred)
        return next(iter(self._providers.values()))
