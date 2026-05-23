from __future__ import annotations

from dataclasses import dataclass
import re

from bioscaffold.immune import PathogenFixture
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.workflow import ProductWorkflowPlan, WorkflowGenePlan


@dataclass(frozen=True)
class ProductRequirement:
    requirement_id: str
    text: str
    artifact_type: str = "code"
    markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompiledProductGenome:
    registry: MoleculeRegistry
    plan: ProductWorkflowPlan
    dna_ref: str
    gene_refs: tuple[str, ...]
    promoter_refs: tuple[str, ...]


class ProductGenomeCompiler:
    def compile(
        self,
        *,
        organism_id: str,
        product_name: str,
        requirements: tuple[ProductRequirement, ...],
        pathogen_fixtures_by_generation: tuple[tuple[PathogenFixture, ...], ...] = (),
    ) -> CompiledProductGenome:
        registry = MoleculeRegistry()
        dna_ref = f"dna.{organism_id}.product_blueprint"
        registry.add(
            MolecularStructure(
                ref=dna_ref,
                molecule_type=MoleculeType.DNA,
                content=product_name,
                markers=("product_blueprint",),
                metadata={
                    "organism_id": organism_id,
                    "product_name": product_name,
                    "requirement_count": len(requirements),
                },
            )
        )

        gene_refs: list[str] = []
        promoter_refs: list[str] = []
        gene_plans: list[WorkflowGenePlan] = []
        for requirement in requirements:
            slug = self._slug(requirement.requirement_id)
            gene_ref = f"gene.{slug}"
            promoter_ref = f"promoter.{slug}"
            registry.add(
                MolecularStructure(
                    ref=gene_ref,
                    molecule_type=MoleculeType.GENE,
                    content=requirement.text,
                    source_refs=(dna_ref,),
                    markers=tuple(dict.fromkeys(requirement.markers)),
                    metadata={
                        "requirement_id": requirement.requirement_id,
                        "artifact_type": requirement.artifact_type,
                    },
                )
            )
            registry.add(
                MolecularStructure(
                    ref=promoter_ref,
                    molecule_type=MoleculeType.PROMOTER,
                    content=f"Activate product requirement: {requirement.text}",
                    source_refs=(gene_ref,),
                    markers=("active",),
                    metadata={"requirement_id": requirement.requirement_id},
                )
            )
            gene_refs.append(gene_ref)
            promoter_refs.append(promoter_ref)
            gene_plans.append(WorkflowGenePlan(gene_ref=gene_ref, promoter_ref=promoter_ref))

        return CompiledProductGenome(
            registry=registry,
            plan=ProductWorkflowPlan(
                organism_id=organism_id,
                product_name=product_name,
                genes=tuple(gene_plans),
                pathogen_fixtures_by_generation=pathogen_fixtures_by_generation,
            ),
            dna_ref=dna_ref,
            gene_refs=tuple(gene_refs),
            promoter_refs=tuple(promoter_refs),
        )

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            raise ValueError("requirement_id must contain at least one alphanumeric character")
        return slug
