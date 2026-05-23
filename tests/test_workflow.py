import pytest

from bioscaffold.generations import Generation, GenerationStatus
from bioscaffold.immune import ImmuneSystem
from bioscaffold.microtasks import AgentHat, MicroOperation, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.organism import OrganismStatus, ProductOrganism
from bioscaffold.turns import TurnStatus
from bioscaffold.workflow import (
    ActiveOrganismRegistry,
    ProductWorkflowPlan,
    ProductWorkflowRunner,
    ProjectWorkflowMicroTaskFactory,
    WorkflowGenePlan,
    WorkflowTerminalState,
)


def seed_registry() -> MoleculeRegistry:
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
            source_refs=("dna.product_blueprint",),
            markers=("auth",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.auth.password_policy",
            molecule_type=MoleculeType.PROMOTER,
            content="Activate password policy work.",
            source_refs=("gene.auth.password_policy",),
            markers=("active",),
        )
    )
    return registry


def seed_registry_with_poisoned_gene() -> MoleculeRegistry:
    registry = seed_registry()
    registry.add(
        MolecularStructure(
            ref="gene.poisoned",
            molecule_type=MoleculeType.GENE,
            content="Fake done output.",
            markers=("fake_completion_marker",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.poisoned",
            molecule_type=MoleculeType.PROMOTER,
            content="Activate poisoned work.",
            markers=("active",),
        )
    )
    return registry


def test_product_workflow_runs_clean_product_to_archived_terminal_state():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),),
        ),
    )

    assert result.terminal_state is WorkflowTerminalState.ARCHIVED
    assert result.organism.status is OrganismStatus.ARCHIVED
    assert result.organism.archive_ref == "archive.organism_000001.000001"
    assert "protein.auth.password_policy.v1" in result.organism.delivered_outputs
    assert [turn.status for turn in result.turns] == [TurnStatus.CLOSED]
    assert [generation.status for generation in result.generations] == [GenerationStatus.REVIEWED]


def test_product_workflow_records_project_microtasks_for_birth_growth_and_death():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),),
        ),
    )
    operations = [(task.operation, task.target_ref) for task in result.project_microtasks]

    assert operations[:3] == [
        (MicroOperation.RECORD, "organism_000001"),
        (MicroOperation.FIND, "gene.auth.password_policy"),
        (MicroOperation.FIND, "promoter.auth.password_policy"),
    ]
    assert (MicroOperation.TRANSCRIBE, "gene.auth.password_policy") in operations
    assert (MicroOperation.SPLICE, "transcript.auth.password_policy.v1") in operations
    assert (MicroOperation.TRANSLATE, "spliced.auth.password_policy.v1") in operations
    assert operations[-2:] == [
        (MicroOperation.PROMOTE, "organism_000001"),
        (MicroOperation.ARCHIVE, "organism_000001"),
    ]
    assert all("docs/superpowers" not in task.target_ref for task in result.project_microtasks)
    assert all("commit" not in task.task_id for task in result.project_microtasks)


def test_product_workflow_missing_gene_blocks_with_project_microtask_evidence():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.missing", "promoter.auth.password_policy"),),
        ),
    )

    assert result.terminal_state is WorkflowTerminalState.BLOCKED
    assert result.organism.status is OrganismStatus.BLOCKED
    assert result.turns[0].tasks[0].task_id == "task.workflow.find_gene.missing"
    assert result.turns[0].tasks[0].state is TaskState.BLOCKED
    assert MicroOperation.TRANSCRIBE not in [task.operation for task in result.turns[0].tasks]
    assert result.project_microtasks[-1].operation is MicroOperation.RECORD
    assert result.project_microtasks[-1].agent_hat is AgentHat.MEMORY_CELL


def test_product_workflow_stops_quarantined_before_delivery():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry_with_poisoned_gene(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.poisoned", "promoter.poisoned"),),
        ),
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
    )

    assert result.terminal_state is WorkflowTerminalState.QUARANTINED
    assert result.organism.status is OrganismStatus.QUARANTINED
    assert result.organism.archive_ref == ""
    assert "quarantined" in result.terminal_reason


def test_product_workflow_reports_failed_terminal_state_for_duplicate_gene_generation():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(
                WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),
                WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),
            ),
        ),
    )

    assert result.terminal_state is WorkflowTerminalState.FAILED
    assert result.organism.status is OrganismStatus.FAILED
    assert result.organism.archive_ref == ""
    assert result.generations[-1].failed_tasks == ("task.transcribe.auth.password_policy",)


def test_product_workflow_returns_blocked_terminal_state_for_empty_gene_plan():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(),
        ),
    )

    assert result.terminal_state is WorkflowTerminalState.BLOCKED
    assert result.organism.status is OrganismStatus.BLOCKED
    assert result.turns == ()
    assert result.generations == ()
    assert result.terminal_reason == "workflow blocked: no genes planned"


def test_active_organism_registry_rejects_second_active_product():
    active = ActiveOrganismRegistry()
    organism = active.begin(
        ProductOrganism.birth(
            organism_id="organism_000001",
            product_name="Authentication Module",
        )
    )

    with pytest.raises(ValueError, match="active organism already exists: organism_000001"):
        active.begin(
            ProductOrganism.birth(
                organism_id="organism_000002",
                product_name="Billing Module",
            )
        )

    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        status=GenerationStatus.REVIEWED,
        promoted_structures=("protein.auth.password_policy.v1",),
    )
    active.finish(organism.integrate_generation(generation).deliver().archive())

    assert active.active_organism_id is None


def test_project_workflow_microtask_factory_finds_real_project_structures():
    tasks = ProjectWorkflowMicroTaskFactory().discovery_tasks(
        seed_registry(),
        gene=WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),
        organism_id="organism_000001",
        generation_id="gen_000001",
        turn_id="turn_000001",
    )

    assert [task.task_id for task in tasks] == [
        "task.workflow.find_gene.auth.password_policy",
        "task.workflow.find_promoter.auth.password_policy",
    ]
    assert [task.state for task in tasks] == [TaskState.COMPLETE, TaskState.COMPLETE]
