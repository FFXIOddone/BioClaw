from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.microtasks import TaskState
from bioscaffold.molecules import MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnStatus


class GenerationStatus(str, Enum):
    OPEN = "open"
    REVIEWED = "reviewed"


@dataclass(frozen=True)
class Generation:
    generation_id: str
    organism_id: str
    turns: tuple[Turn, ...] = ()
    status: GenerationStatus = GenerationStatus.OPEN
    promoted_structures: tuple[str, ...] = ()
    quarantined_structures: tuple[str, ...] = ()
    immune_memory: tuple[str, ...] = ()


class GenerationEngine:
    def review(self, generation: Generation, registry: MoleculeRegistry) -> Generation:
        open_turns = [turn.turn_id for turn in generation.turns if turn.status is not TurnStatus.CLOSED]
        if open_turns:
            raise ValueError(
                f"generation review requires closed turns: {', '.join(open_turns)}"
            )

        promoted = []
        quarantined = []
        for turn in generation.turns:
            for task in turn.tasks:
                if task.state is TaskState.COMPLETE:
                    promoted.extend(task.outputs)
                if task.state is TaskState.QUARANTINED:
                    quarantined.extend(task.outputs or (task.target_ref,))

        quarantined_refs = set(quarantined)
        promoted = [
            ref
            for ref in promoted
            if ref not in quarantined_refs and self._is_promotable(registry, ref)
        ]

        immune_memory = tuple(
            structure.ref
            for structure in registry.find_by_type(MoleculeType.ANTIBODY)
        )
        return replace(
            generation,
            status=GenerationStatus.REVIEWED,
            promoted_structures=tuple(dict.fromkeys(promoted)),
            quarantined_structures=tuple(dict.fromkeys(quarantined)),
            immune_memory=immune_memory,
        )

    def _is_promotable(self, registry: MoleculeRegistry, ref: str) -> bool:
        try:
            structure = registry.get(ref)
        except KeyError:
            return False
        if structure.molecule_type in {MoleculeType.PLASMID, MoleculeType.ANTIGEN}:
            return False
        if "pathogen_fixture" in structure.markers:
            return False
        return True
