from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MoleculeType(str, Enum):
    DNA = "dna"
    GENE = "gene"
    PROMOTER = "promoter"
    RNA_TRANSCRIPT = "rna_transcript"
    SPLICED_TRANSCRIPT = "spliced_transcript"
    PLASMID = "plasmid"
    PROTEIN = "protein"
    ANTIGEN = "antigen"
    ANTIBODY = "antibody"


@dataclass(frozen=True)
class MolecularStructure:
    ref: str
    molecule_type: MoleculeType
    content: str
    source_refs: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class MoleculeRegistry:
    def __init__(self) -> None:
        self._structures: dict[str, MolecularStructure] = {}

    def add(self, structure: MolecularStructure) -> MolecularStructure:
        if structure.ref in self._structures:
            raise ValueError(f"duplicate molecular structure ref: {structure.ref}")
        self._structures[structure.ref] = structure
        return structure

    def get(self, ref: str) -> MolecularStructure:
        return self._structures[ref]

    def find_by_type(self, molecule_type: MoleculeType) -> tuple[MolecularStructure, ...]:
        return tuple(
            structure
            for structure in self._structures.values()
            if structure.molecule_type is molecule_type
        )

    def all(self) -> tuple[MolecularStructure, ...]:
        return tuple(self._structures.values())
