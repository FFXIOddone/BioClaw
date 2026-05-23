from __future__ import annotations

from bioscaffold.types import BudgetReport, CheckpointResult


class CheckpointSuite:
    def __init__(self, *, min_health_score: float) -> None:
        self._min_health_score = min_health_score

    def evaluate(
        self,
        *,
        health_score: float,
        genome_valid: bool,
        budget_report: BudgetReport,
        audit_event_count: int,
    ) -> CheckpointResult:
        if health_score < self._min_health_score:
            return CheckpointResult(False, "health score below threshold")
        if not genome_valid:
            return CheckpointResult(False, "genome validation failed")
        if budget_report.is_exhausted:
            return CheckpointResult(False, "budget exhausted")
        if audit_event_count <= 0:
            return CheckpointResult(False, "audit ledger is empty")
        return CheckpointResult(True, "all checkpoints passed")
