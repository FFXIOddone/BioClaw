from bioscaffold.all_generation import AllGenerationProductRunner, ProductBuildRequest
from bioscaffold.assembly import ProductAssemblyEngine
from bioscaffold.compiler import ProductGenomeCompiler, ProductRequirement
from bioscaffold.delivery import DeliveryPackager
from bioscaffold.generations import Generation, GenerationEngine
from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.proposals import ProposalPlanner
from bioscaffold.turns import Turn, TurnEngine
from bioscaffold.validation import ArtifactValidationEngine
from bioscaffold.workflow import WorkflowTerminalState


def test_product_request_compiles_to_dna_genes_promoters_and_workflow_plan():
    compiled = ProductGenomeCompiler().compile(
        organism_id="organism_000001",
        product_name="Authentication Module",
        requirements=(
            ProductRequirement(
                requirement_id="password-policy",
                text="Require password policy.",
                artifact_type="code",
            ),
        ),
    )

    assert compiled.dna_ref == "dna.organism_000001.product_blueprint"
    assert compiled.gene_refs == ("gene.password_policy",)
    assert compiled.promoter_refs == ("promoter.password_policy",)
    assert compiled.plan.genes[0].gene_ref == "gene.password_policy"
    assert compiled.registry.get("gene.password_policy").metadata["artifact_type"] == "code"
    assert compiled.registry.get("promoter.password_policy").markers == ("active",)


def test_proposal_planner_materializes_generation_proposals_as_project_microtasks():
    blocked_task = MicroTask(
        task_id="task.workflow.find_gene.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.missing",
        agent_hat=AgentHat.GENE_SCOUT,
    ).with_terminal(TaskState.BLOCKED, reason="missing project gene")
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(blocked_task,),
        )
    )
    generation = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        MoleculeRegistry(),
    )

    tasks = ProposalPlanner().materialize(
        generation,
        turn_id="turn_000002",
        generation_id="gen_000002",
    )

    assert [task.operation for task in tasks] == [MicroOperation.FIND]
    assert tasks[0].agent_hat is AgentHat.GENE_SCOUT
    assert tasks[0].state is TaskState.COMPLETE
    assert tasks[0].metadata["source_task_id"] == "task.workflow.find_gene.missing"


def test_validation_engine_creates_antibody_memory_for_invalid_artifact_marker():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="protein.fake_done.v1",
            molecule_type=MoleculeType.PROTEIN,
            content="artifact fragment: fake done",
            markers=("artifact_fragment", "fake_completion_marker"),
        )
    )

    result = ArtifactValidationEngine(invalid_markers={"fake_completion_marker"}).validate_all(
        registry,
        artifact_refs=("protein.fake_done.v1",),
        organism_id="organism_000001",
        generation_id="gen_000001",
        turn_id="turn_000001",
    )

    assert result.quarantined_refs == ("protein.fake_done.v1",)
    assert result.antibody_refs == ("antibody.fake_completion_marker",)
    assert registry.get("antibody.fake_completion_marker").molecule_type is MoleculeType.ANTIBODY
    assert result.tasks[0].state is TaskState.QUARANTINED


def test_assembly_engine_promotes_validated_artifacts_up_scale_ladder():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="protein.password_policy.v1",
            molecule_type=MoleculeType.PROTEIN,
            content="artifact fragment: Require password policy.",
            markers=("artifact_fragment",),
        )
    )

    result = ProductAssemblyEngine().assemble(
        registry,
        organism_id="organism_000001",
        artifact_refs=("protein.password_policy.v1",),
    )

    assert result.module_ref == "module.organism_000001.v1"
    assert result.subsystem_ref == "subsystem.organism_000001.v1"
    assert result.capability_ref == "capability.organism_000001.v1"
    assert registry.get(result.module_ref).molecule_type is MoleculeType.MODULE
    assert [task.operation for task in result.tasks] == [
        MicroOperation.PROMOTE,
        MicroOperation.PROMOTE,
        MicroOperation.PROMOTE,
    ]


def test_all_generation_runner_completes_product_request_to_delivery_report():
    result = AllGenerationProductRunner().run(
        ProductBuildRequest(
            organism_id="organism_000001",
            product_name="Authentication Module",
            requirements=(
                ProductRequirement(
                    requirement_id="password-policy",
                    text="Require password policy.",
                    artifact_type="code",
                ),
            ),
        )
    )

    assert result.workflow_result.terminal_state is WorkflowTerminalState.ARCHIVED
    assert result.delivery_report.archive_ref == "archive.organism_000001.000001"
    assert result.delivery_report.organism_id == "organism_000001"
    assert result.delivery_report.generation_ids == ("gen_000001",)
    assert result.assembly.capability_ref in result.delivery_report.assembly_refs
    assert result.validation.validated_refs == ("protein.password_policy.v1",)
    assert result.proposal_tasks == ()
    assert MicroOperation.VALIDATE in [task.operation for task in result.project_microtasks]
    assert MicroOperation.PROMOTE in [task.operation for task in result.project_microtasks]
    assert MicroOperation.ARCHIVE in [task.operation for task in result.project_microtasks]


def test_delivery_packager_preserves_terminal_lineage_and_task_evidence():
    result = AllGenerationProductRunner().run(
        ProductBuildRequest(
            organism_id="organism_000001",
            product_name="Authentication Module",
            requirements=(
                ProductRequirement(
                    requirement_id="password-policy",
                    text="Require password policy.",
                ),
            ),
        )
    )

    report = DeliveryPackager().package(
        workflow_result=result.workflow_result,
        validation=result.validation,
        assembly=result.assembly,
        project_microtasks=result.project_microtasks,
    )

    assert report.terminal_state is WorkflowTerminalState.ARCHIVED
    assert report.task_ids[0] == "task.workflow.birth.organism_000001"
    assert "task.validate.protein.password_policy.v1" in report.task_ids
    assert report.archive_ref == result.workflow_result.organism.archive_ref
