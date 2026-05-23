from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.assembly import ProductAssemblyResult
from bioscaffold.microtasks import MicroTask
from bioscaffold.validation import ArtifactValidationResult
from bioscaffold.workflow import ProductWorkflowResult, WorkflowTerminalState


@dataclass(frozen=True)
class DeliveryReport:
    organism_id: str
    terminal_state: WorkflowTerminalState
    archive_ref: str
    delivered_outputs: tuple[str, ...]
    generation_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    immune_event_ids: tuple[str, ...]
    assembly_refs: tuple[str, ...]
    validation_task_ids: tuple[str, ...]
    proposal_task_ids: tuple[str, ...]


class DeliveryPackager:
    def package(
        self,
        *,
        workflow_result: ProductWorkflowResult,
        validation: ArtifactValidationResult,
        assembly: ProductAssemblyResult,
        project_microtasks: tuple[MicroTask, ...],
        proposal_tasks: tuple[MicroTask, ...] = (),
    ) -> DeliveryReport:
        return DeliveryReport(
            organism_id=workflow_result.organism.organism_id,
            terminal_state=workflow_result.terminal_state,
            archive_ref=workflow_result.organism.archive_ref,
            delivered_outputs=workflow_result.organism.delivered_outputs,
            generation_ids=workflow_result.organism.generation_ids,
            task_ids=tuple(task.task_id for task in project_microtasks),
            immune_event_ids=tuple(event.event_id for event in workflow_result.immune_events),
            assembly_refs=assembly.assembly_refs,
            validation_task_ids=tuple(task.task_id for task in validation.tasks),
            proposal_task_ids=tuple(task.task_id for task in proposal_tasks),
        )
