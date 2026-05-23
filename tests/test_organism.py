import pytest

from bioscaffold.generations import Generation, GenerationStatus
from bioscaffold.organism import OrganismStatus, ProductOrganism


def reviewed_generation(
    *,
    promoted: tuple[str, ...] = ("protein.auth.password_policy.v1",),
    quarantined: tuple[str, ...] = (),
) -> Generation:
    return Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        status=GenerationStatus.REVIEWED,
        promoted_structures=promoted,
        quarantined_structures=quarantined,
    )


def test_product_organism_birth_records_product_start():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    assert organism.status is OrganismStatus.BORN
    assert organism.product_name == "Authentication Module"
    assert organism.generation_ids == ()


def test_product_organism_delivers_and_archives_reviewed_growth():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    grown = organism.integrate_generation(reviewed_generation())
    delivered = grown.deliver()
    archived = delivered.archive()

    assert grown.status is OrganismStatus.GROWING
    assert delivered.status is OrganismStatus.DELIVERED
    assert delivered.delivered_outputs == ("protein.auth.password_policy.v1",)
    assert archived.status is OrganismStatus.ARCHIVED
    assert archived.archive_ref == "archive.organism_000001.000001"


def test_product_organism_refuses_delivery_with_quarantined_growth():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    quarantined = organism.integrate_generation(
        reviewed_generation(
            promoted=(),
            quarantined=("plasmid.injected.fake_done.v1",),
        )
    )

    assert quarantined.status is OrganismStatus.QUARANTINED
    with pytest.raises(ValueError, match="quarantined organism cannot be delivered"):
        quarantined.deliver()


def test_product_organism_requires_reviewed_generation():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    with pytest.raises(ValueError, match="only reviewed generations can be integrated"):
        organism.integrate_generation(
            Generation(generation_id="gen_000001", organism_id="organism_000001")
        )
