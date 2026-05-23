from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bioscaffold.generations import Generation
from bioscaffold.growth import GrowthCycleRunner
from bioscaffold.immune import ImmuneEvent, ImmuneSystem, PathogenFixture
from bioscaffold.molecules import MoleculeRegistry
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


class ProductWorkflowRunner:
    def __init__(
        self,
        *,
        growth_runner: GrowthCycleRunner | None = None,
        active_registry: ActiveOrganismRegistry | None = None,
    ) -> None:
        self.growth_runner = growth_runner or GrowthCycleRunner()
        self.active_registry = active_registry or ActiveOrganismRegistry()

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

        if not plan.genes:
            organism = self.active_registry.finish(organism.block())
            return ProductWorkflowResult(
                registry=registry,
                organism=organism,
                turns=(),
                generations=(),
                immune_events=(),
                terminal_state=WorkflowTerminalState.BLOCKED,
                terminal_reason="workflow blocked: no genes planned",
            )

        for index, gene in enumerate(plan.genes, start=1):
            result = self.growth_runner.run_generation(
                registry=registry,
                organism=organism,
                gene_ref=gene.gene_ref,
                promoter_ref=gene.promoter_ref,
                generation_id=f"gen_{index:06d}",
                turn_id=f"turn_{index:06d}",
                immune_system=immune_system,
                pathogen_fixtures=self._pathogen_fixtures_for(plan, index),
            )
            organism = result.organism
            turns.append(result.turn)
            generations.append(result.generation)
            immune_events.extend(result.immune_events)

            terminal_state = self._terminal_state_for(organism)
            if terminal_state is not None:
                self.active_registry.finish(organism)
                return ProductWorkflowResult(
                    registry=registry,
                    organism=organism,
                    turns=tuple(turns),
                    generations=tuple(generations),
                    immune_events=tuple(immune_events),
                    terminal_state=terminal_state,
                    terminal_reason=self._terminal_reason(organism, generations[-1]),
                )

        organism = self.active_registry.finish(organism.deliver().archive())
        return ProductWorkflowResult(
            registry=registry,
            organism=organism,
            turns=tuple(turns),
            generations=tuple(generations),
            immune_events=tuple(immune_events),
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
