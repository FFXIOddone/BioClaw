import pytest

from bioscaffold.microtasks import (
    AgentHat,
    AgentHatPolicy,
    BioScale,
    MicroOperation,
    MicroTask,
    TaskState,
)


def test_microtask_terminal_transition_records_outputs():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
        inputs=("genome.product_requirements",),
        expected_output="located_gene_ref",
    )

    terminal = task.with_terminal(
        TaskState.COMPLETE,
        reason="gene located",
        outputs=("gene.auth.password_policy",),
    )

    assert terminal.is_terminal is True
    assert terminal.state is TaskState.COMPLETE
    assert terminal.reason == "gene located"
    assert terminal.outputs == ("gene.auth.password_policy",)


def test_microtask_rejects_non_terminal_transition():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    with pytest.raises(ValueError, match="state must be terminal"):
        task.with_terminal(TaskState.RUNNING, reason="still working")


def test_microtask_requires_terminal_reason():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    with pytest.raises(ValueError, match="terminal reason is required"):
        task.with_terminal(TaskState.FAILED, reason="")


def test_agent_hat_policy_allows_declared_operation():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.SPLICE,
        target_ref="transcript.auth.password_policy",
        agent_hat=AgentHat.SPLICER,
    )

    decision = AgentHatPolicy.default().authorize(task)

    assert decision.allowed is True


def test_agent_hat_policy_rejects_out_of_scope_operation():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.INJECT,
        target_ref="transcript.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    decision = AgentHatPolicy.default().authorize(task)

    assert decision.allowed is False
    assert decision.reason == "hat gene_scout cannot perform inject"
