import pytest

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.turns import Turn, TurnEngine, TurnProposal, TurnStatus


def make_task(task_id: str, state: TaskState = TaskState.PENDING) -> MicroTask:
    task = MicroTask(
        task_id=task_id,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref=f"gene.{task_id}",
        agent_hat=AgentHat.GENE_SCOUT,
    )
    if state is TaskState.PENDING:
        return task
    return task.with_terminal(state, reason=f"{state.value} evidence", outputs=(f"output.{task_id}",))


def test_turn_cannot_close_with_non_terminal_tasks():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(make_task("task_000001"),),
    )

    with pytest.raises(ValueError, match="non-terminal tasks: task_000001"):
        TurnEngine().close(turn)


def test_turn_closes_when_all_tasks_are_terminal():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_000001", TaskState.COMPLETE),
            make_task("task_000002", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert closed.status is TurnStatus.CLOSED
    assert closed.terminal_counts == {
        "complete": 1,
        "failed": 0,
        "blocked": 0,
        "quarantined": 1,
    }
    assert closed.outputs == ("output.task_000001", "output.task_000002")


def test_turn_rejects_unauthorized_hat_operation():
    task = MicroTask(
        task_id="task.bad.inject",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.INJECT,
        target_ref="plasmid.bad",
        agent_hat=AgentHat.GENE_SCOUT,
    ).with_terminal(TaskState.COMPLETE, reason="bad injection", outputs=("plasmid.bad",))

    with pytest.raises(ValueError, match="hat gene_scout cannot perform inject"):
        TurnEngine().close(
            Turn(
                turn_id="turn_000001",
                generation_id="gen_000001",
                organism_id="organism_000001",
                tasks=(task,),
            )
        )


def test_turn_derives_next_turn_proposals_from_failed_blocked_and_quarantined_tasks():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_failed", TaskState.FAILED),
            make_task("task_blocked", TaskState.BLOCKED),
            make_task("task_quarantined", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert [proposal.source_task_id for proposal in closed.next_turn_proposals] == [
        "task_failed",
        "task_blocked",
        "task_quarantined",
    ]
    assert [proposal.recommended_operation for proposal in closed.next_turn_proposals] == [
        MicroOperation.VALIDATE,
        MicroOperation.FIND,
        MicroOperation.NEUTRALIZE,
    ]


def test_turn_rejects_legacy_string_proposals():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(make_task("task_000001", TaskState.COMPLETE),),
        next_turn_proposals=("legacy proposal",),
    )

    with pytest.raises(ValueError, match="next_turn_proposals must contain TurnProposal"):
        TurnEngine().close(turn)


def test_turn_close_is_idempotent_for_next_turn_proposals():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(make_task("task_failed", TaskState.FAILED),),
    )

    once = TurnEngine().close(turn)
    twice = TurnEngine().close(once)

    assert twice.next_turn_proposals == once.next_turn_proposals
    assert len(twice.next_turn_proposals) == 1


def test_turn_preserves_preseeded_structured_proposals():
    proposal = TurnProposal(
        source_task_id="task_prior",
        target_ref="gene.prior",
        source_state=TaskState.BLOCKED,
        recommended_operation=MicroOperation.FIND,
        recommended_hat=AgentHat.GENE_SCOUT,
        reason="prior blocked evidence",
    )
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(make_task("task_000001", TaskState.COMPLETE),),
        next_turn_proposals=(proposal,),
    )

    closed = TurnEngine().close(turn)

    assert closed.next_turn_proposals == (proposal,)


def test_turn_preserves_failed_blocked_and_quarantined_evidence():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_failed", TaskState.FAILED),
            make_task("task_blocked", TaskState.BLOCKED),
            make_task("task_quarantined", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert [task.reason for task in closed.tasks] == [
        "failed evidence",
        "blocked evidence",
        "quarantined evidence",
    ]
