from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CellRole(str, Enum):
    SENSOR = "sensor"
    WORKER = "worker"
    MEMORY = "memory"
    REPAIR = "repair"
    LYSOSOME = "lysosome"
    IMMUNE = "immune"
    PLANNER = "planner"
    GOVERNOR = "governor"


class LifecyclePhase(str, Enum):
    G0 = "G0"
    G1 = "G1"
    S = "S"
    G2 = "G2"
    M = "M"
    CYTOKINESIS = "cytokinesis"
    APOPTOTIC = "apoptotic"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    parent_ids: tuple[str, ...]
    generation: int
    source_genome_hash: str
    snapshot_id: str
    role: CellRole
    permission_profile: str

    @classmethod
    def root(
        cls,
        *,
        cell_id: str,
        genome_hash: str,
        snapshot_id: str,
        role: CellRole,
        permission_profile: str,
    ) -> "CellIdentity":
        return cls(
            cell_id=cell_id,
            parent_ids=(),
            generation=0,
            source_genome_hash=genome_hash,
            snapshot_id=snapshot_id,
            role=role,
            permission_profile=permission_profile,
        )

    def child(self, *, cell_id: str, snapshot_id: str, permission_profile: str) -> "CellIdentity":
        return CellIdentity(
            cell_id=cell_id,
            parent_ids=(self.cell_id,),
            generation=self.generation + 1,
            source_genome_hash=self.source_genome_hash,
            snapshot_id=snapshot_id,
            role=self.role,
            permission_profile=permission_profile,
        )


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str

    @classmethod
    def allow(cls, reason: str = "allowed") -> "PolicyDecision":
        return cls(True, reason)

    @classmethod
    def deny(cls, reason: str) -> "PolicyDecision":
        return cls(False, reason)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str = "valid"


@dataclass(frozen=True)
class BudgetReport:
    runtime_seconds_remaining: float
    memory_mb_remaining: float
    tokens_remaining: int
    api_cost_usd_remaining: float

    @property
    def is_exhausted(self) -> bool:
        return (
            self.runtime_seconds_remaining <= 0
            or self.memory_mb_remaining <= 0
            or self.tokens_remaining < 0
            or self.api_cost_usd_remaining < 0
        )


@dataclass(frozen=True)
class BudgetRequest:
    runtime_seconds: float = 0.0
    memory_mb: float = 0.0
    tokens: int = 0
    api_cost_usd: float = 0.0


@dataclass(frozen=True)
class BudgetReservation:
    reservation_id: str
    request: BudgetRequest
    accepted: bool
    reason: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    cell_id: str
    event_type: str
    lifecycle_phase: LifecyclePhase
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Job:
    job_id: str
    payload: dict[str, Any]
    required_runtime_seconds: float = 0.0
    required_memory_mb: float = 0.0


@dataclass(frozen=True)
class JobResult:
    job_id: str
    succeeded: bool
    output: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class CheckpointResult:
    passed: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SnapshotRef:
    snapshot_id: str
    genome_hash: str
