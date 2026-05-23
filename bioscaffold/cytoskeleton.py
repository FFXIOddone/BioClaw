from __future__ import annotations

from bioscaffold.types import PolicyDecision


class Cytoskeleton:
    def __init__(self) -> None:
        self._routes: set[tuple[str, str]] = set()

    @property
    def routes(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._routes))

    def register_route(self, source: str, target: str) -> PolicyDecision:
        route = (source, target)
        if route in self._routes:
            return PolicyDecision.deny(f"route {source}->{target} already exists")
        self._routes.add(route)
        return PolicyDecision.allow(f"route {source}->{target} registered")
