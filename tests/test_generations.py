import pytest

from bioscaffold.generations import Generation, GenerationEngine, GenerationStatus
from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnEngine


def terminal_task(task_id: str, state: TaskState, output: str) -> MicroTask:
    return MicroTask(
        task_id=task_id,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.VALIDATE,
        target_ref=output,
        agent_hat=AgentHat.VALIDATOR,
    ).with_terminal(state, reason=f"{state.value} evidence", outputs=(output,))


def test_generation_review_requires_closed_turns():
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(Turn(turn_id="turn_000001", generation_id="gen_000001", organism_id="organism_000001"),),
    )

    with pytest.raises(ValueError, match="generation review requires closed turns"):
        GenerationEngine().review(generation, MoleculeRegistry())


def test_generation_review_promotes_only_closed_turn_outputs():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
        )
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(terminal_task("task_000001", TaskState.COMPLETE, "gene.auth.password_policy"),),
        )
    )
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(turn,),
    )

    reviewed = GenerationEngine().review(generation, registry)

    assert reviewed.status is GenerationStatus.REVIEWED
    assert reviewed.promoted_structures == ("gene.auth.password_policy",)
    assert reviewed.quarantined_structures == ()


def test_generation_review_preserves_quarantine_and_immune_memory():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="antibody.fake_completion_marker",
            molecule_type=MoleculeType.ANTIBODY,
            content="signature for fake completion marker",
            markers=("fake_completion_marker",),
        )
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(
                terminal_task(
                    "task_000001",
                    TaskState.QUARANTINED,
                    "plasmid.injected.fake_done.v1",
                ),
            ),
        )
    )
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(turn,),
    )

    reviewed = GenerationEngine().review(generation, registry)

    assert reviewed.promoted_structures == ()
    assert reviewed.quarantined_structures == ("plasmid.injected.fake_done.v1",)
    assert reviewed.immune_memory == ("antibody.fake_completion_marker",)
