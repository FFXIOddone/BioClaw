from bioscaffold.audit import AuditLedger
from bioscaffold.types import LifecyclePhase


def test_audit_ledger_appends_events_with_stable_ids():
    ledger = AuditLedger(cell_id="cell_000001")

    event = ledger.record(
        event_type="checkpoint_passed",
        lifecycle_phase=LifecyclePhase.G2,
        reason="all gates passed",
        metadata={"health_score": 0.95},
    )

    assert event.event_id == "audit_000001"
    assert event.cell_id == "cell_000001"
    assert ledger.events == (event,)


def test_audit_ledger_exposes_immutable_tuple():
    ledger = AuditLedger(cell_id="cell_000001")
    ledger.record(
        event_type="started",
        lifecycle_phase=LifecyclePhase.G0,
        reason="cell initialized",
    )

    assert isinstance(ledger.events, tuple)
