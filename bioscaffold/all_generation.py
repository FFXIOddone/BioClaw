from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.assembly import ProductAssemblyEngine, ProductAssemblyResult
from bioscaffold.compiler import (
    CompiledProductGenome,
    ProductGenomeCompiler,
    ProductRequirement,
)
from bioscaffold.delivery import DeliveryPackager, DeliveryReport
from bioscaffold.immune import ImmuneSystem, PathogenFixture
from bioscaffold.microtasks import MicroTask
from bioscaffold.molecules import MoleculeType
from bioscaffold.proposals import ProposalPlanner
from bioscaffold.validation import ArtifactValidationEngine, ArtifactValidationResult
from bioscaffold.workflow import ProductWorkflowResult, ProductWorkflowRunner


@dataclass(frozen=True)
class ProductBuildRequest:
    organism_id: str
    product_name: str
    requirements: tuple[ProductRequirement, ...]
    known_immune_markers: tuple[str, ...] = ()
    pathogen_fixtures_by_generation: tuple[tuple[PathogenFixture, ...], ...] = ()


@dataclass(frozen=True)
class AllGenerationWorkflowResult:
    compiled: CompiledProductGenome
    workflow_result: ProductWorkflowResult
    proposal_tasks: tuple[MicroTask, ...]
    validation: ArtifactValidationResult
    assembly: ProductAssemblyResult
    delivery_report: DeliveryReport
    project_microtasks: tuple[MicroTask, ...]


class AllGenerationProductRunner:
    def __init__(
        self,
        *,
        compiler: ProductGenomeCompiler | None = None,
        workflow_runner: ProductWorkflowRunner | None = None,
        proposal_planner: ProposalPlanner | None = None,
        validation_engine: ArtifactValidationEngine | None = None,
        assembly_engine: ProductAssemblyEngine | None = None,
        delivery_packager: DeliveryPackager | None = None,
    ) -> None:
        self.compiler = compiler or ProductGenomeCompiler()
        self.workflow_runner = workflow_runner or ProductWorkflowRunner()
        self.proposal_planner = proposal_planner or ProposalPlanner()
        self.validation_engine = validation_engine or ArtifactValidationEngine()
        self.assembly_engine = assembly_engine or ProductAssemblyEngine()
        self.delivery_packager = delivery_packager or DeliveryPackager()

    def run(self, request: ProductBuildRequest) -> AllGenerationWorkflowResult:
        compiled = self.compiler.compile(
            organism_id=request.organism_id,
            product_name=request.product_name,
            requirements=request.requirements,
            pathogen_fixtures_by_generation=request.pathogen_fixtures_by_generation,
        )
        workflow_result = self.workflow_runner.run_to_terminal(
            registry=compiled.registry,
            plan=compiled.plan,
            immune_system=self._immune_system_for(request),
        )
        proposal_tasks = self._materialize_generation_proposals(workflow_result)
        validation = self.validation_engine.validate_all(
            compiled.registry,
            artifact_refs=self._protein_artifacts(workflow_result),
            organism_id=request.organism_id,
            generation_id="validation",
            turn_id="validation",
        )
        assembly = self.assembly_engine.assemble(
            compiled.registry,
            organism_id=request.organism_id,
            artifact_refs=validation.validated_refs,
        )
        project_microtasks = (
            *workflow_result.project_microtasks,
            *proposal_tasks,
            *validation.tasks,
            *assembly.tasks,
        )
        delivery_report = self.delivery_packager.package(
            workflow_result=workflow_result,
            validation=validation,
            assembly=assembly,
            project_microtasks=project_microtasks,
            proposal_tasks=proposal_tasks,
        )
        return AllGenerationWorkflowResult(
            compiled=compiled,
            workflow_result=workflow_result,
            proposal_tasks=proposal_tasks,
            validation=validation,
            assembly=assembly,
            delivery_report=delivery_report,
            project_microtasks=project_microtasks,
        )

    def _immune_system_for(self, request: ProductBuildRequest) -> ImmuneSystem | None:
        if not request.known_immune_markers:
            return None
        return ImmuneSystem(known_markers=set(request.known_immune_markers))

    def _materialize_generation_proposals(
        self,
        workflow_result: ProductWorkflowResult,
    ) -> tuple[MicroTask, ...]:
        materialized: list[MicroTask] = []
        for index, generation in enumerate(workflow_result.generations, start=1):
            materialized.extend(
                self.proposal_planner.materialize(
                    generation,
                    turn_id=f"turn.proposal.{index:06d}",
                    generation_id=f"gen.proposal.{index:06d}",
                    organism_id=workflow_result.organism.organism_id,
                )
            )
        return tuple(materialized)

    def _protein_artifacts(self, workflow_result: ProductWorkflowResult) -> tuple[str, ...]:
        artifact_refs = []
        for output_ref in workflow_result.organism.delivered_outputs:
            try:
                structure = workflow_result.registry.get(output_ref)
            except KeyError:
                continue
            if structure.molecule_type is MoleculeType.PROTEIN:
                artifact_refs.append(output_ref)
        return tuple(dict.fromkeys(artifact_refs))
