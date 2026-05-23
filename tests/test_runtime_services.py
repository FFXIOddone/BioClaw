from bioscaffold.cytoskeleton import Cytoskeleton
from bioscaffold.genome import Genome
from bioscaffold.membrane import Membrane
from bioscaffold.mitochondria import Mitochondria
from bioscaffold.nucleus import Nucleus
from bioscaffold.ribosome import Ribosome
from bioscaffold.types import BudgetRequest, CellRole, Job


def test_genome_validates_and_snapshots_config():
    genome = Genome(
        {
            "genome_id": "genome_base_v0_1",
            "version": "0.1.0",
            "allowed_roles": ["worker"],
            "allowed_paths": ["./sandbox"],
            "budgets": {"max_runtime_seconds": 30, "max_memory_mb": 256},
        }
    )

    validation = genome.validate()
    snapshot = genome.snapshot()

    assert validation.valid is True
    assert snapshot.snapshot_id == "snapshot_000001"
    assert snapshot.genome_hash.startswith("sha256:")


def test_nucleus_denies_permission_escalation():
    nucleus = Nucleus(
        allowed_actions={"execute_job"},
        permission_profile="sandbox_worker",
    )

    decision = nucleus.authorize("grant_admin")

    assert decision.allowed is False
    assert decision.reason == "action grant_admin is not allowed"


def test_nucleus_assigns_root_identity():
    nucleus = Nucleus(
        allowed_actions={"execute_job"},
        permission_profile="sandbox_worker",
    )

    identity = nucleus.assign_identity(
        genome_hash="sha256:abc",
        snapshot_id="snapshot_000001",
        role=CellRole.WORKER,
    )

    assert identity.cell_id == "cell_000001"
    assert identity.role is CellRole.WORKER


def test_membrane_rejects_unknown_input_key():
    membrane = Membrane(allowed_input_keys={"job_id"}, allowed_output_keys={"result"})

    result = membrane.validate_input({"job_id": "job_1", "extra": True})

    assert result.valid is False
    assert result.reason == "unknown input keys: extra"


def test_mitochondria_denies_over_budget_request():
    mitochondria = Mitochondria(max_runtime_seconds=10, max_memory_mb=128)

    reservation = mitochondria.reserve(BudgetRequest(runtime_seconds=11, memory_mb=1))

    assert reservation.accepted is False
    assert reservation.reason == "runtime budget exceeded"


def test_mitochondria_reports_remaining_budget_after_reservation():
    mitochondria = Mitochondria(max_runtime_seconds=10, max_memory_mb=128)

    reservation = mitochondria.reserve(BudgetRequest(runtime_seconds=2, memory_mb=8))
    report = mitochondria.report()

    assert reservation.accepted is True
    assert report.runtime_seconds_remaining == 8
    assert report.memory_mb_remaining == 120


def test_ribosome_executes_allowed_fake_job():
    ribosome = Ribosome(allowed_job_types={"echo"})

    result = ribosome.execute(Job(job_id="job_000001", payload={"type": "echo", "value": "ok"}))

    assert result.succeeded is True
    assert result.output == {"result": "ok"}


def test_ribosome_rejects_unknown_job_type():
    ribosome = Ribosome(allowed_job_types={"echo"})

    result = ribosome.execute(Job(job_id="job_000001", payload={"type": "shell", "value": "no"}))

    assert result.succeeded is False
    assert result.reason == "job type shell is not allowed"


def test_cytoskeleton_rejects_duplicate_route():
    graph = Cytoskeleton()

    first = graph.register_route("ribosome", "lysosome")
    second = graph.register_route("ribosome", "lysosome")

    assert first.allowed is True
    assert second.allowed is False
    assert second.reason == "route ribosome->lysosome already exists"
