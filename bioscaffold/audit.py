from __future__ import annotations

from bioscaffold.types import AuditEvent, LifecyclePhase


class AuditLedger:
    def __init__(self, *, cell_id: str) -> None:
        self._cell_id = cell_id
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        *,
        event_type: str,
        lifecycle_phase: LifecyclePhase,
        reason: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"audit_{len(self._events) + 1:06d}",
            cell_id=self._cell_id,
            event_type=event_type,
            lifecycle_phase=lifecycle_phase,
            reason=reason,
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        return event
