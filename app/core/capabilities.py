"""A registry mapping capability names to the components that provide them.

Capabilities are named like `document.pdf.read`. Built-in components and,
later, extensions register through the same registry, so the core never
hard-codes which component handles what (Decision 028).
"""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class CapabilityNotAvailableError(LookupError):
    """Raised when no component provides a requested capability."""

    def __init__(self, capability: str) -> None:
        self.capability = capability
        super().__init__(f"No component provides the capability '{capability}'.")


class CapabilityRegistry(Generic[T]):
    """Registers providers by capability name.

    Registering a second provider for the same capability replaces the
    first, which lets an extension supersede a built-in implementation.
    """

    def __init__(self) -> None:
        self._providers: dict[str, T] = {}

    def register(self, capability: str, provider: T) -> None:
        self._providers[capability] = provider

    def get(self, capability: str) -> T:
        try:
            return self._providers[capability]
        except KeyError:
            raise CapabilityNotAvailableError(capability) from None

    def has(self, capability: str) -> bool:
        return capability in self._providers

    @property
    def capabilities(self) -> list[str]:
        return sorted(self._providers)
