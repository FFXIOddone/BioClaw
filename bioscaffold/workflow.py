from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bioscaffold.generations import Generation
from bioscaffold.growth import GrowthCycleRunner
from bioscaffold.immune import ImmuneEvent, ImmuneSystem, PathogenFixture
from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MoleculeRegistry, MoleculeType
from bioscaffold.organism import OrganismStatus, ProductOrganism
from bioscaffold.turns import Turn


class WorkflowTerminalState(str, Enum):
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowGenePlan:
    gene_ref: str
    promoter_ref: str


@dataclass(frozen=True)
class ProductWorkflowPlan:
    organism_id: str
    product_name: str
    genes: tuple[WorkflowGenePlan, ...]
    pathogen_fixtures_by_generation: tuple[tuple[PathogenFixture, ...], ...] = ()


@dataclass(frozen=True)
class ProductWorkflowResult:
    registry: MoleculeRegistry
    organism: ProductOrganism
    turns: tuple[Turn, ...]
    generations: tuple[Generation, ...]
    immune_events: tuple[ImmuneEvent, ...]
    project_microtasks: tuple[MicroTask, ...]
    terminal_state: WorkflowTerminalState
    terminal_reason: str


TERMINAL_ORGANISM_STATUSES = frozenset(
    {
        OrganismStatus.ARCHIVED,
        OrganismStatus.QUARANTINED,
        OrganismStatus.BLOCKED,
        OrganismStatus.FAILED,
    }
)


class ActiveOrganismRegistry:
    def __init__(self) -> None:
        self._active: ProductOrganism | None = None

    @property
    def active_organism_id(self) -> str | None:
        if self._active is None:
            return None
        return self._active.organism_id

    def begin(self, organism: ProductOrganism) -> ProductOrganism:
        if self._active is not None and self._active.status not in TERMINAL_ORGANISM_STATUSES:
            raise ValueError(f"active organism already exists: {self._active.organism_id}")
        self._active = organism
        return organism

    def finish(self, organism: ProductOrganism) -> ProductOrganism:
        if self._active is None:
            raise ValueError("no active organism to finish")
        if organism.organism_id != self._active.organism_id:
            raise ValueError("finished organism does not match active organism")
        if organism.status not in TERMINAL_ORGANISM_STATUSES:
            raise ValueError("only terminal organisms can finish the active workflow")
        self._active = None
        return organism


class ProjectWorkflowMicroTaskFactory:
    def birth_task(self, organism: ProductOrganism) -> MicroTask:
        return MicroTask(
            task_id=f"task.workflow.birth.{organism.organism_id}",
            turn_id="workflow",
            generation_id="workflow",
            organism_id=organism.organism_id,
            scale=BioScale.ORGANISM,
            operation=MicroOperation.RECORD,
            target_ref=organism.organism_id,
            agent_hat=AgentHat.MEMORY_CELL,
            expected_output="born_product_organism",
            metadata={"project_workflow": True, "workflow_phase": "birth"},
        ).with_terminal(
            TaskState.COMPLETE,
            reason="product organism born",
            outputs=(organism.organism_id,),
        )

    def discovery_tasks(
        self,
        registry: MoleculeRegistry,
        *,
        gene: WorkflowGenePlan,
        organism_id: str,
        generation_id: str,
        turn_id: str,
    ) -> tuple[MicroTask, ...]:
        return (
            self._find_structure_task(
                registry,
                task_id=f"task.workflow.find_gene.{self._typed_suffix(gene.gene_ref, 'gene')}",
                target_ref=gene.gene_ref,
                molecule_type=MoleculeType.GENE,
                expected_output="gene_ref",
                reason="project gene located",
                organism_id=organism_id,
                generation_id=generation_id,
                turn_id=turn_id,
            ),
            self._find_structure_task(
                registry,
                task_id=(
                    "task.workflow.find_promoter."
                    f"{self._typed_suffix(gene.promoter_ref, 'promoter')}"
                ),
                target_ref=gene.promoter_ref,
                molecule_type=MoleculeType.PROMOTER,
                expected_output="promoter_ref",
                reason="project promoter located",
                organism_id=organism_id,
                generation_id=generation_id,
                turn_id=turn_id,
            ),
        )

    def delivery_task(self, organism: ProductOrganism) -> MicroTask:
        return MicroTask(
            task_id=f"task.workflow.deliver.{organism.organism_id}",
            turn_id="workflow",
            generation_id="workflow",
            organism_id=organism.organism_id,
            scale=BioScale.ORGANISM,
            operation=MicroOperation.PROMOTE,
            target_ref=organism.organism_id,
            agent_hat=AgentHat.GENERATION_REVIEWER,
            expected_output="delivered_product",
            metadata={"project_workflow": True, "workflow_phase": "delivery"},
        ).with_terminal(
            TaskState.COMPLETE,
            reason="product delivered",
            outputs=organism.delivered_outputs,
        )

    def archive_task(self, organism: ProductOrganism) -> MicroTask:
        return MicroTask(
            task_id=f"task.workflow.archive.{organism.organism_id}",
            turn_id="workflow",
            generation_id="workflow",
            organism_id=organism.organism_id,
            scale=BioScale.ORGANISM,
            operation=MicroOperation.ARCHIVE,
            target_ref=organism.organism_id,
            agent_hat=AgentHat.GENERATION_REVIEWER,
            expected_output="archive_ref",
            metadata={"project_workflow": True, "workflow_phase": "archive"},
        ).with_terminal(
            TaskState.COMPLETE,
            reason="product archived",
            outputs=(organism.archive_ref,),
        )

    def terminal_record_task(
        self,
        organism: ProductOrganism,
        *,
        terminal_state: WorkflowTerminalState,
        reason: str,
    ) -> MicroTask:
        state = {
            WorkflowTerminalState.QUARANTINED: TaskState.QUARANTINED,
            WorkflowTerminalState.BLOCKED: TaskState.BLOCKED,
            WorkflowTerminalState.FAILED: TaskState.FAILED,
            WorkflowTerminalState.ARCHIVED: TaskState.COMPLETE,
        }[terminal_state]
        return MicroTask(
            task_id=f"task.workflow.terminal.{terminal_state.value}.{organism.organism_id}",
            turn_id="workflow",
            generation_id="workflow",
            organism_id=organism.organism_id,
            scale=BioScale.ORGANISM,
            operation=MicroOperation.RECORD,
            target_ref=organism.organism_id,
            agent_hat=AgentHat.MEMORY_CELL,
            expected_output="terminal_workflow_state",
            metadata={"project_workflow": True, "workflow_phase": "terminal"},
        ).with_terminal(state, reason=reason, outputs=(organism.organism_id,))

    def _find_structure_task(
        self,
        registry: MoleculeRegistry,
        *,
        task_id: str,
        target_ref: str,
        molecule_type: MoleculeType,
        expected_output: str,
        reason: str,
        organism_id: str,
        generation_id: str,
        turn_id: str,
    ) -> MicroTask:
        task = MicroTask(
            task_id=task_id,
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.MOLECULAR,
            operation=MicroOperation.FIND,
            target_ref=target_ref,
            agent_hat=AgentHat.GENE_SCOUT,
            expected_output=expected_output,
            metadata={"project_workflow": True, "workflow_phase": "discovery"},
        )
        try:
            structure = registry.get(target_ref)
        except KeyError:
            return task.with_terminal(
                TaskState.BLOCKED,
                reason=f"missing project workflow input: {target_ref}",
            )
        if structure.molecule_type is not molecule_type:
            return task.with_terminal(
                TaskState.FAILED,
                reason=f"{target_ref} is not a {molecule_type.value}",
            )
        return task.with_terminal(TaskState.COMPLETE, reason=reason, outputs=(target_ref,))

    def _typed_suffix(self, ref: str, prefix: str) -> str:
        typed_prefix = f"{prefix}."
        if ref.startswith(typed_prefix):
            return ref[len(typed_prefix) :]
        return ref.split(".", 1)[1] if "." in ref else ref


class ProductWorkflowRunner:
    def __init__(
        self,
        *,
        growth_runner: GrowthCycleRunner | None = None,
        active_registry: ActiveOrganismRegistry | None = None,
        microtask_factory: ProjectWorkflowMicroTaskFactory | None = None,
    ) -> None:
        self.growth_runner = growth_runner or GrowthCycleRunner()
        self.active_registry = active_registry or ActiveOrganismRegistry()
        self.microtask_factory = microtask_factory or ProjectWorkflowMicroTaskFactory()

    def run_to_terminal(
        self,
        *,
        registry: MoleculeRegistry,
        plan: ProductWorkflowPlan,
        immune_system: ImmuneSystem | None = None,
    ) -> ProductWorkflowResult:
        organism = self.active_registry.begin(
            ProductOrganism.birth(
                organism_id=plan.organism_id,
                product_name=plan.product_name,
            )
        )
        turns: list[Turn] = []
        generations: list[Generation] = []
        immune_events: list[ImmuneEvent] = []
        project_microtasks: list[MicroTask] = [self.microtask_factory.birth_task(organism)]

        if not plan.genes:
            organism = self.active_registry.finish(organism.block())
            terminal_state = WorkflowTerminalState.BLOCKED
            terminal_reason = "workflow blocked: no genes planned"
            project_microtasks.append(
                self.microtask_factory.terminal_record_task(
                    organism,
                    terminal_state=terminal_state,
                    reason=terminal_reason,
                )
            )
            return ProductWorkflowResult(
                registry=registry,
                organism=organism,
                turns=(),
                generations=(),
                immune_events=(),
                project_microtasks=tuple(project_microtasks),
                terminal_state=terminal_state,
                terminal_reason=terminal_reason,
            )

        for index, gene in enumerate(plan.genes, start=1):
            generation_id = f"gen_{index:06d}"
            turn_id = f"turn_{index:06d}"
            prefix_tasks = self.microtask_factory.discovery_tasks(
                registry,
                gene=gene,
                organism_id=organism.organism_id,
                generation_id=generation_id,
                turn_id=turn_id,
            )
            result = self.growth_runner.run_generation(
                registry=registry,
                organism=organism,
                gene_ref=gene.gene_ref,
                promoter_ref=gene.promoter_ref,
                generation_id=generation_id,
                turn_id=turn_id,
                immune_system=immune_system,
                pathogen_fixtures=self._pathogen_fixtures_for(plan, index),
                prefix_tasks=prefix_tasks,
            )
            organism = result.organism
            turns.append(result.turn)
            generations.append(result.generation)
            immune_events.extend(result.immune_events)
            project_microtasks.extend(result.turn.tasks)

            terminal_state = self._terminal_state_for(organism)
            if terminal_state is not None:
                terminal_reason = self._terminal_reason(organism, generations[-1])
                project_microtasks.append(
                    self.microtask_factory.terminal_record_task(
                        organism,
                        terminal_state=terminal_state,
                        reason=terminal_reason,
                    )
                )
                self.active_registry.finish(organism)
                return ProductWorkflowResult(
                    registry=registry,
                    organism=organism,
                    turns=tuple(turns),
                    generations=tuple(generations),
                    immune_events=tuple(immune_events),
                    project_microtasks=tuple(project_microtasks),
                    terminal_state=terminal_state,
                    terminal_reason=terminal_reason,
                )

        delivered = organism.deliver()
        archived = delivered.archive()
        project_microtasks.append(self.microtask_factory.delivery_task(delivered))
        project_microtasks.append(self.microtask_factory.archive_task(archived))
        organism = self.active_registry.finish(archived)
        return ProductWorkflowResult(
            registry=registry,
            organism=organism,
            turns=tuple(turns),
            generations=tuple(generations),
            immune_events=tuple(immune_events),
            project_microtasks=tuple(project_microtasks),
            terminal_state=WorkflowTerminalState.ARCHIVED,
            terminal_reason="product delivered and archived",
        )

    def _pathogen_fixtures_for(
        self,
        plan: ProductWorkflowPlan,
        generation_index: int,
    ) -> tuple[PathogenFixture, ...]:
        fixture_index = generation_index - 1
        if fixture_index >= len(plan.pathogen_fixtures_by_generation):
            return ()
        return plan.pathogen_fixtures_by_generation[fixture_index]

    def _terminal_state_for(
        self,
        organism: ProductOrganism,
    ) -> WorkflowTerminalState | None:
        if organism.status is OrganismStatus.QUARANTINED:
            return WorkflowTerminalState.QUARANTINED
        if organism.status is OrganismStatus.BLOCKED:
            return WorkflowTerminalState.BLOCKED
        if organism.status is OrganismStatus.FAILED:
            return WorkflowTerminalState.FAILED
        return None

    def _terminal_reason(
        self,
        organism: ProductOrganism,
        generation: Generation,
    ) -> str:
        if organism.status is OrganismStatus.QUARANTINED:
            return f"organism quarantined: {', '.join(organism.quarantined_structures)}"
        if organism.status is OrganismStatus.BLOCKED:
            return f"organism blocked: {', '.join(generation.blocked_tasks)}"
        if organism.status is OrganismStatus.FAILED:
            return f"organism failed: {', '.join(generation.failed_tasks)}"
        return "product delivered and archived"
