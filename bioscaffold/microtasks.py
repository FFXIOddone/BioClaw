from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from bioscaffold.types import PolicyDecision


class BioScale(str, Enum):
    MOLECULAR = "molecular"
    PROTEIN = "protein"
    CELL = "cell"
    TISSUE = "tissue"
    ORGAN = "organ"
    ORGANISM = "organism"


class MicroOperation(str, Enum):
    FIND = "find"
    COPY = "copy"
    SPLICE = "splice"
    BIND = "bind"
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"
    PRODUCE = "produce"
    VALIDATE = "validate"
    INJECT = "inject"
    DETECT = "detect"
    QUARANTINE = "quarantine"
    NEUTRALIZE = "neutralize"
    RECORD = "record"
    PROMOTE = "promote"
    ARCHIVE = "archive"


class AgentHat(str, Enum):
    GENE_SCOUT = "gene_scout"
    SPLICER = "splicer"
    TRANSCRIBER = "transcriber"
    RIBOSOME_WORKER = "ribosome_worker"
    VALIDATOR = "validator"
    BACTERIA = "bacteria"
    WHITE_BLOOD_CELL = "white_blood_cell"
    MACROPHAGE = "macrophage"
    MEMORY_CELL = "memory_cell"
    GENERATION_REVIEWER = "generation_reviewer"


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"


TERMINAL_STATES = frozenset(
    {
        TaskState.COMPLETE,
        TaskState.FAILED,
        TaskState.BLOCKED,
        TaskState.QUARANTINED,
    }
)


@dataclass(frozen=True)
class MicroTask:
    task_id: str
    turn_id: str
    generation_id: str
    organism_id: str
    scale: BioScale
    operation: MicroOperation
    target_ref: str
    agent_hat: AgentHat
    inputs: tuple[str, ...] = ()
    expected_output: str = ""
    state: TaskState = TaskState.PENDING
    reason: str = ""
    outputs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def with_terminal(
        self,
        state: TaskState,
        *,
        reason: str,
        outputs: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> "MicroTask":
        if state not in TERMINAL_STATES:
            raise ValueError("state must be terminal")
        if not reason:
            raise ValueError("terminal reason is required")
        merged_metadata = dict(self.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return replace(
            self,
            state=state,
            reason=reason,
            outputs=tuple(outputs),
            metadata=merged_metadata,
        )


@dataclass(frozen=True)
class AgentHatPolicy:
    allowed_operations: dict[AgentHat, frozenset[MicroOperation]]

    @classmethod
    def default(cls) -> "AgentHatPolicy":
        return cls(
            allowed_operations={
                AgentHat.GENE_SCOUT: frozenset({MicroOperation.FIND, MicroOperation.RECORD}),
                AgentHat.SPLICER: frozenset({MicroOperation.SPLICE, MicroOperation.VALIDATE}),
                AgentHat.TRANSCRIBER: frozenset(
                    {MicroOperation.COPY, MicroOperation.TRANSCRIBE}
                ),
                AgentHat.RIBOSOME_WORKER: frozenset(
                    {MicroOperation.BIND, MicroOperation.TRANSLATE, MicroOperation.PRODUCE}
                ),
                AgentHat.VALIDATOR: frozenset(
                    {MicroOperation.VALIDATE, MicroOperation.RECORD}
                ),
                AgentHat.BACTERIA: frozenset({MicroOperation.INJECT, MicroOperation.RECORD}),
                AgentHat.WHITE_BLOOD_CELL: frozenset(
                    {
                        MicroOperation.DETECT,
                        MicroOperation.QUARANTINE,
                        MicroOperation.NEUTRALIZE,
                    }
                ),
                AgentHat.MACROPHAGE: frozenset(
                    {MicroOperation.QUARANTINE, MicroOperation.ARCHIVE}
                ),
                AgentHat.MEMORY_CELL: frozenset(
                    {MicroOperation.RECORD, MicroOperation.PROMOTE}
                ),
                AgentHat.GENERATION_REVIEWER: frozenset(
                    {MicroOperation.VALIDATE, MicroOperation.PROMOTE, MicroOperation.ARCHIVE}
                ),
            }
        )

    def authorize(self, task: MicroTask) -> PolicyDecision:
        allowed = self.allowed_operations.get(task.agent_hat, frozenset())
        if task.operation not in allowed:
            return PolicyDecision.deny(
                f"hat {task.agent_hat.value} cannot perform {task.operation.value}"
            )
        return PolicyDecision.allow("hat operation allowed")
