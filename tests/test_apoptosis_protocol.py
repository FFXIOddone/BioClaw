from bioscaffold.cell import BioCell
from bioscaffold.lysosome import Lysosome
from bioscaffold.types import CellRole, LifecyclePhase


def test_lysosome_archives_before_reclaim():
    lysosome = Lysosome(destructive_delete=False)

    receipt = lysosome.collect("failed_output", {"job_id": "job_000001"})
    result = lysosome.reclaim()

    assert receipt.archive_ref == "archive_000001"
    assert result["reclaimed_count"] == 1
    assert result["destructive_delete"] is False
    assert lysosome.archives == (("archive_000001", "failed_output", {"job_id": "job_000001"}),)


def test_lysosome_dry_run_preserves_items():
    lysosome = Lysosome(destructive_delete=False)

    lysosome.collect("stale_job", {"job_id": "job_000002"})
    lysosome.reclaim()

    assert len(lysosome.archives) == 1


def test_apoptosis_stops_new_work_and_records_reason():
    cell = BioCell.bootstrap(role=CellRole.WORKER)

    result = cell.apoptose("policy violation")
    job_result = cell.run_job({"job_id": "job_000001", "type": "echo", "value": "blocked"})

    assert result["phase"] == LifecyclePhase.APOPTOTIC
    assert job_result.succeeded is False
    assert job_result.reason == "cell is not active"
    assert cell.audit_events[-1].event_type == "job_rejected"
