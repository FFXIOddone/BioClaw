from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.microtasks import MicroTask, TaskState


class TurnStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class Turn:
    turn_id: str
    generation_id: str
    organism_id: str
    tasks: tuple[MicroTask, ...] = ()
    status: TurnStatus = TurnStatus.OPEN
    outputs: tuple[str, ...] = ()
    immune_events: tuple[str, ...] = ()
    next_turn_proposals: tuple[str, ...] = ()

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
    def close(self, turn: Turn) -> Turn:
        non_terminal = [task.task_id for task in turn.tasks if not task.is_terminal]
        if non_terminal:
            raise ValueError(f"turn cannot close with non-terminal tasks: {', '.join(non_terminal)}")
        outputs = tuple(output for task in turn.tasks for output in task.outputs)
        return replace(turn, status=TurnStatus.CLOSED, outputs=outputs)
