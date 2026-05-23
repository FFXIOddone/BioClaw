import pytest

from bioscaffold.immune import ImmuneSystem, PathogenFixture
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


def test_generation_review_does_not_promote_missing_output_refs():
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(terminal_task("task_ghost", TaskState.COMPLETE, "structure.missing"),),
        )
    )

    reviewed = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        MoleculeRegistry(),
    )

    assert reviewed.promoted_structures == ()


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


def test_generation_review_quarantines_pathogen_target_without_promoting_plasmid():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )
    injection_task = fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    immune_task, _event = ImmuneSystem(known_markers={"fake_completion_marker"}).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v1",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(injection_task, immune_task),
        )
    )

    reviewed = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        registry,
    )

    assert "plasmid.injected.fake_done.v1" in reviewed.quarantined_structures
    assert "plasmid.injected.fake_done.v1" not in reviewed.promoted_structures
    assert reviewed.immune_memory == ("antibody.fake_completion_marker",)


def test_generation_review_records_blocked_failed_and_next_generation_proposals():
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(
                terminal_task("task_blocked", TaskState.BLOCKED, "gene.blocked"),
                terminal_task("task_failed", TaskState.FAILED, "gene.failed"),
            ),
        )
    )

    reviewed = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        MoleculeRegistry(),
    )

    assert reviewed.blocked_tasks == ("task_blocked",)
    assert reviewed.failed_tasks == ("task_failed",)
    assert [proposal.source_task_id for proposal in reviewed.next_generation_proposals] == [
        "task_blocked",
        "task_failed",
    ]
