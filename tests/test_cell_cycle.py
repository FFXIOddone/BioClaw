from bioscaffold.checkpoints import CheckpointSuite
from bioscaffold.lifecycle import LifecyclePolicy
from bioscaffold.types import BudgetReport, LifecyclePhase


def test_lifecycle_policy_allows_ordered_growth_path():
    policy = LifecyclePolicy()

    assert policy.can_transition(LifecyclePhase.G0, LifecyclePhase.G1).allowed is True
    assert policy.can_transition(LifecyclePhase.G1, LifecyclePhase.S).allowed is True
    assert policy.can_transition(LifecyclePhase.S, LifecyclePhase.G2).allowed is True


def test_lifecycle_policy_rejects_mitosis_without_g2():
    policy = LifecyclePolicy()

    decision = policy.can_transition(LifecyclePhase.G1, LifecyclePhase.M)

    assert decision.allowed is False
    assert decision.reason == "transition G1->M is not allowed"


def test_checkpoint_suite_passes_healthy_cell_state():
    checkpoints = CheckpointSuite(min_health_score=0.8)

    result = checkpoints.evaluate(
        health_score=0.9,
        genome_valid=True,
        budget_report=BudgetReport(1, 1, 0, 0),
        audit_event_count=3,
    )

    assert result.passed is True


def test_checkpoint_suite_rejects_low_health():
    checkpoints = CheckpointSuite(min_health_score=0.8)

    result = checkpoints.evaluate(
        health_score=0.7,
        genome_valid=True,
        budget_report=BudgetReport(1, 1, 0, 0),
        audit_event_count=3,
    )

    assert result.passed is False
    assert result.reason == "health score below threshold"
