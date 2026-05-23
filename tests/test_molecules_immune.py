import pytest

from bioscaffold.immune import ImmuneSystem, PathogenFixture
from bioscaffold.microtasks import TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


def test_molecule_registry_stores_and_finds_structures():
    registry = MoleculeRegistry()
    gene = MolecularStructure(
        ref="gene.auth.password_policy",
        molecule_type=MoleculeType.GENE,
        content="Require a password policy.",
        source_refs=("dna.product_blueprint",),
        markers=("auth",),
    )

    registry.add(gene)

    assert registry.get("gene.auth.password_policy") == gene
    assert registry.find_by_type(MoleculeType.GENE) == (gene,)


def test_molecule_registry_rejects_duplicate_refs():
    registry = MoleculeRegistry()
    gene = MolecularStructure(
        ref="gene.auth.password_policy",
        molecule_type=MoleculeType.GENE,
        content="Require a password policy.",
    )
    registry.add(gene)

    with pytest.raises(ValueError, match="duplicate molecular structure ref"):
        registry.add(gene)


def test_pathogen_fixture_injects_inert_plasmid():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )

    task = fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    plasmid = registry.get("plasmid.injected.fake_done.v1")
    assert plasmid.molecule_type is MoleculeType.PLASMID
    assert plasmid.markers == ("fake_completion_marker", "pathogen_fixture")
    assert task.state is TaskState.COMPLETE
    assert task.outputs == ("plasmid.injected.fake_done.v1",)


def test_white_blood_cell_quarantines_known_marker():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )
    fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    task, event = ImmuneSystem(known_markers={"fake_completion_marker"}).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v1",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.QUARANTINED
    assert event.action == "quarantine"
    assert event.antibody_ref == "antibody.fake_completion_marker"
    assert registry.get("antibody.fake_completion_marker").molecule_type is MoleculeType.ANTIBODY
