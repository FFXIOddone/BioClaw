from bioscaffold.generations import GenerationStatus
from bioscaffold.growth import GrowthCycleRunner
from bioscaffold.immune import ImmuneSystem, PathogenFixture
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.organism import OrganismStatus, ProductOrganism
from bioscaffold.turns import TurnStatus


def seed_expression_registry() -> MoleculeRegistry:
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


def test_growth_cycle_runs_expression_and_clean_delivery_path():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=organism,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
    )
    archived = result.organism.deliver().archive()

    assert result.turn.status is TurnStatus.CLOSED
    assert result.generation.status is GenerationStatus.REVIEWED
    assert "protein.auth.password_policy.v1" in result.generation.promoted_structures
    assert result.organism.status is OrganismStatus.GROWING
    assert archived.status is OrganismStatus.ARCHIVED


def test_growth_cycle_injects_bacteria_and_quarantines_with_immune_memory():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=organism,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
        pathogen_fixtures=(fixture,),
    )

    assert result.organism.status is OrganismStatus.QUARANTINED
    assert "protein.auth.password_policy.v1" in result.generation.promoted_structures
    assert "plasmid.injected.fake_done.v1" in result.generation.quarantined_structures
    assert "plasmid.injected.fake_done.v1" not in result.generation.promoted_structures
    detect_task_ids = [task.task_id for task in result.turn.tasks if task.task_id.startswith("task.detect.")]

    assert result.generation.immune_memory == ("antibody.fake_completion_marker",)
    assert result.turn.immune_events.count("immune.quarantine.plasmid.injected.fake_done.v1") == 1
    assert "immune.clean.transcript.auth.password_policy.v1" in result.turn.immune_events
    assert len(detect_task_ids) == len(set(detect_task_ids))


def test_growth_cycle_quarantines_normal_outputs_with_known_immune_markers():
    registry = seed_expression_registry()
    registry.add(
        MolecularStructure(
            ref="antibody.fake_completion_marker",
            molecule_type=MoleculeType.ANTIBODY,
            content="signature for fake done",
            markers=("fake_completion_marker",),
        )
    )
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
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    result = GrowthCycleRunner().run_generation(
        registry=registry,
        organism=organism,
        gene_ref="gene.poisoned",
        promoter_ref="promoter.poisoned",
        generation_id="gen_000001",
        turn_id="turn_000001",
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
    )

    assert "transcript.poisoned.v1" in result.generation.quarantined_structures
    assert "spliced.poisoned.v1" in result.generation.quarantined_structures
    assert "transcript.poisoned.v1" not in result.generation.promoted_structures
    assert "spliced.poisoned.v1" not in result.generation.promoted_structures
    assert result.organism.status is OrganismStatus.QUARANTINED
