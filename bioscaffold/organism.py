from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.generations import Generation, GenerationStatus


class OrganismStatus(str, Enum):
    PLANNED = "planned"
    BORN = "born"
    GROWING = "growing"
    DELIVERED = "delivered"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class ProductOrganism:
    organism_id: str
    product_name: str
    status: OrganismStatus = OrganismStatus.PLANNED
    generation_ids: tuple[str, ...] = ()
    stable_structures: tuple[str, ...] = ()
    quarantined_structures: tuple[str, ...] = ()
    delivered_outputs: tuple[str, ...] = ()
    archive_ref: str = ""

    @classmethod
    def birth(cls, *, organism_id: str, product_name: str) -> "ProductOrganism":
        return cls(
            organism_id=organism_id,
            product_name=product_name,
            status=OrganismStatus.BORN,
        )

    def integrate_generation(self, generation: Generation) -> "ProductOrganism":
        if generation.status is not GenerationStatus.REVIEWED:
            raise ValueError("only reviewed generations can be integrated")
        if generation.organism_id != self.organism_id:
            raise ValueError("generation belongs to a different organism")
        generation_ids = (*self.generation_ids, generation.generation_id)
        stable = tuple(dict.fromkeys((*self.stable_structures, *generation.promoted_structures)))
        quarantined = tuple(
            dict.fromkeys((*self.quarantined_structures, *generation.quarantined_structures))
        )
        status = OrganismStatus.QUARANTINED if quarantined else OrganismStatus.GROWING
        return replace(
            self,
            status=status,
            generation_ids=generation_ids,
            stable_structures=stable,
            quarantined_structures=quarantined,
        )

    def deliver(self) -> "ProductOrganism":
        if self.status is OrganismStatus.QUARANTINED:
            raise ValueError("quarantined organism cannot be delivered")
        if not self.stable_structures:
            raise ValueError("organism has no stable structures to deliver")
        return replace(
            self,
            status=OrganismStatus.DELIVERED,
            delivered_outputs=self.stable_structures,
        )

    def archive(self) -> "ProductOrganism":
        if self.status is not OrganismStatus.DELIVERED:
            raise ValueError("only delivered organisms can be archived")
        return replace(
            self,
            status=OrganismStatus.ARCHIVED,
            archive_ref=f"archive.{self.organism_id}.{len(self.generation_ids):06d}",
        )
