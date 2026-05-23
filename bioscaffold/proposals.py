from __future__ import annotations

from bioscaffold.generations import Generation
from bioscaffold.microtasks import BioScale, MicroTask, TaskState


class ProposalPlanner:
    def materialize(
        self,
        generation: Generation,
        *,
        turn_id: str,
        generation_id: str | None = None,
        organism_id: str | None = None,
    ) -> tuple[MicroTask, ...]:
        materialized = []
        for index, proposal in enumerate(generation.next_generation_proposals, start=1):
            materialized.append(
                MicroTask(
                    task_id=(
                        f"task.proposal.{index:06d}."
                        f"{proposal.recommended_operation.value}.{proposal.source_task_id}"
                    ),
                    turn_id=turn_id,
                    generation_id=generation_id or generation.generation_id,
                    organism_id=organism_id or generation.organism_id,
                    scale=BioScale.MOLECULAR,
                    operation=proposal.recommended_operation,
                    target_ref=proposal.target_ref,
                    agent_hat=proposal.recommended_hat,
                    expected_output="materialized_project_microtask",
                    metadata={
                        "project_workflow": True,
                        "workflow_phase": "proposal",
                        "source_task_id": proposal.source_task_id,
                        "source_state": proposal.source_state.value,
                        "source_reason": proposal.reason,
                    },
                ).with_terminal(
                    TaskState.COMPLETE,
                    reason=f"proposal materialized from {proposal.source_task_id}",
                    outputs=(proposal.target_ref,),
                )
            )
        return tuple(materialized)
