from __future__ import annotations

from bioscaffold.cell import BioCell
from bioscaffold.types import LifecyclePhase, ReplicationResult


class ReproductionController:
    def __init__(self, *, max_children_per_cycle: int = 1) -> None:
        self._max_children_per_cycle = max_children_per_cycle
        self._child_counts: dict[str, int] = {}

    def mitosis(self, parent: BioCell) -> ReplicationResult:
        if parent.phase is not LifecyclePhase.G2:
            return ReplicationResult(False, "parent must be in G2 before mitosis")

        current_count = self._child_counts.get(parent.identity.cell_id, 0)
        if current_count >= self._max_children_per_cycle:
            return ReplicationResult(False, "max children per cycle reached")

        validation = parent.genome.validate()
        checkpoint = parent.checkpoints.evaluate(
            health_score=0.95,
            genome_valid=validation.valid,
            budget_report=parent.mitochondria.report(),
            audit_event_count=len(parent.audit_events),
        )
        if not checkpoint.passed:
            return ReplicationResult(False, checkpoint.reason)

        snapshot = parent.genome.snapshot()
        child_number = current_count + 1
        child_id = f"{parent.identity.cell_id}_child_{child_number:06d}"
        child = parent.spawn_child(child_id=child_id, snapshot_id=snapshot.snapshot_id)
        self._child_counts[parent.identity.cell_id] = child_number
        parent.audit.record(
            event_type="mitosis_completed",
            lifecycle_phase=parent.phase,
            reason="child created in sandbox",
            metadata={"child_id": child.identity.cell_id},
        )
        return ReplicationResult(True, "child created", child)
