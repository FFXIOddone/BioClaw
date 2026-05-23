from bioscaffold.lysosome import Lysosome


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
