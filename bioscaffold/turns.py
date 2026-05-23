from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.microtasks import (
    AgentHat,
    AgentHatPolicy,
    MicroOperation,
    MicroTask,
    TaskState,
)


class TurnStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class TurnProposal:
    source_task_id: str
    target_ref: str
    source_state: TaskState
    recommended_operation: MicroOperation
    recommended_hat: AgentHat
    reason: str


@dataclass(frozen=True)
class Turn:
    turn_id: str
    generation_id: str
    organism_id: str
    tasks: tuple[MicroTask, ...] = ()
    status: TurnStatus = TurnStatus.OPEN
    outputs: tuple[str, ...] = ()
    immune_events: tuple[str, ...] = ()
    next_turn_proposals: tuple[TurnProposal, ...] = ()

    @property
    def terminal_counts(self) -> dict[str, int]:
        return {
            TaskState.COMPLETE.value: sum(1 for task in self.tasks if task.state is TaskState.COMPLETE),
            TaskState.FAILED.value: sum(1 for task in self.tasks if task.state is TaskState.FAILED),
            TaskState.BLOCKED.value: sum(1 for task in self.tasks if task.state is TaskState.BLOCKED),
            TaskState.QUARANTINED.value: sum(
                1 for task in self.tasks if task.state is TaskState.QUARANTINED
            ),
        }


class TurnEngine:
    def __init__(self, *, policy: AgentHatPolicy | None = None) -> None:
        self.policy = policy or AgentHatPolicy.default()

    def close(self, turn: Turn) -> Turn:
        non_terminal = [task.task_id for task in turn.tasks if not task.is_terminal]
        if non_terminal:
            raise ValueError(f"turn cannot close with non-terminal tasks: {', '.join(non_terminal)}")
        denied = [
            f"{task.task_id}: {decision.reason}"
            for task in turn.tasks
            if not (decision := self.policy.authorize(task)).allowed
        ]
        if denied:
            raise ValueError(f"turn contains unauthorized tasks: {', '.join(denied)}")
        outputs = tuple(output for task in turn.tasks for output in task.outputs)
        self._validate_proposals(turn.next_turn_proposals)
        proposals = self._dedupe_proposals(
            (*turn.next_turn_proposals, *self._derive_proposals(turn.tasks))
        )
        return replace(
            turn,
            status=TurnStatus.CLOSED,
            outputs=outputs,
            next_turn_proposals=proposals,
        )

    def _derive_proposals(self, tasks: tuple[MicroTask, ...]) -> tuple[TurnProposal, ...]:
        proposals = []
        for task in tasks:
            recommendation = self._recommendation_for(task)
            if recommendation is None:
                continue
            operation, hat = recommendation
            proposals.append(
                TurnProposal(
                    source_task_id=task.task_id,
                    target_ref=task.target_ref,
                    source_state=task.state,
                    recommended_operation=operation,
                    recommended_hat=hat,
                    reason=task.reason,
                )
            )
        return tuple(proposals)

    def _recommendation_for(
        self,
        task: MicroTask,
    ) -> tuple[MicroOperation, AgentHat] | None:
        if task.state is TaskState.FAILED:
            return MicroOperation.VALIDATE, AgentHat.VALIDATOR
        if task.state is TaskState.BLOCKED:
            return MicroOperation.FIND, AgentHat.GENE_SCOUT
        if task.state is TaskState.QUARANTINED:
            return MicroOperation.NEUTRALIZE, AgentHat.WHITE_BLOOD_CELL
        return None

    def _validate_proposals(self, proposals: tuple[TurnProposal, ...]) -> None:
        if any(not isinstance(proposal, TurnProposal) for proposal in proposals):
            raise ValueError("next_turn_proposals must contain TurnProposal entries")

    def _dedupe_proposals(
        self,
        proposals: tuple[TurnProposal, ...],
    ) -> tuple[TurnProposal, ...]:
        return tuple(dict.fromkeys(proposals))
