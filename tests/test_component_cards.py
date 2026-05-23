from pathlib import Path

from bioscaffold.cards import load_registry
from bioscaffold.types import (
    BudgetReport,
    CellIdentity,
    CellRole,
    LifecyclePhase,
    PolicyDecision,
)


def test_package_imports():
    import bioscaffold

    assert bioscaffold.__all__ == [
        "ActiveOrganismRegistry",
        "AgentHat",
        "BioCell",
        "BioScale",
        "CellRole",
        "ExpressionEngine",
        "Generation",
        "GenerationEngine",
        "GrowthCycleResult",
        "GrowthCycleRunner",
        "LifecyclePhase",
        "MicroOperation",
        "MicroTask",
        "MolecularStructure",
        "MoleculeRegistry",
        "MoleculeType",
        "OrganismStatus",
        "ProductOrganism",
        "ProductWorkflowPlan",
        "ProductWorkflowResult",
        "ProductWorkflowRunner",
        "TaskState",
        "Turn",
        "TurnEngine",
        "TurnProposal",
        "WorkflowGenePlan",
        "WorkflowTerminalState",
    ]


def test_cell_identity_has_lineage_metadata():
    identity = CellIdentity.root(
        cell_id="cell_000001",
        genome_hash="sha256:abc",
        snapshot_id="snapshot_000001",
        role=CellRole.WORKER,
        permission_profile="sandbox_worker",
    )

    assert identity.cell_id == "cell_000001"
    assert identity.parent_ids == ()
    assert identity.generation == 0
    assert identity.source_genome_hash == "sha256:abc"
    assert identity.snapshot_id == "snapshot_000001"
    assert identity.role is CellRole.WORKER


def test_budget_report_detects_exhaustion():
    report = BudgetReport(
        runtime_seconds_remaining=0.0,
        memory_mb_remaining=12.0,
        tokens_remaining=0,
        api_cost_usd_remaining=0.0,
    )

    assert report.is_exhausted is True


def test_policy_decision_denial_has_reason():
    decision = PolicyDecision.deny("outside membrane policy")

    assert decision.allowed is False
    assert decision.reason == "outside membrane policy"


def test_all_repository_cards_are_valid():
    registry = load_registry(Path("bio_components"))

    names = {card.name for card in registry}

    assert names == {
        "antibody",
        "antigen",
        "apoptosis",
        "autophagy",
        "cytoskeleton",
        "dna",
        "endoplasmic-reticulum",
        "gene",
        "golgi-apparatus",
        "growth-cycle",
        "immune-response",
        "lysosome",
        "meiosis",
        "mitochondria",
        "mitosis",
        "nucleus",
        "plasma-membrane",
        "plasmid",
        "product-organism",
        "ribosome",
        "rna-transcript",
        "splicing",
        "transcription",
        "translation",
    }
    assert all(card.human_review_required for card in registry)
