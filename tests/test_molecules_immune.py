import pytest

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
