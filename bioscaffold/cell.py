from __future__ import annotations

from bioscaffold.audit import AuditLedger
from bioscaffold.checkpoints import CheckpointSuite
from bioscaffold.genome import Genome
from bioscaffold.lysosome import Lysosome
from bioscaffold.membrane import Membrane
from bioscaffold.mitochondria import Mitochondria
from bioscaffold.nucleus import Nucleus
from bioscaffold.ribosome import Ribosome
from bioscaffold.types import (
    BudgetRequest,
    CellIdentity,
    CellRole,
    Job,
    JobResult,
    LifecyclePhase,
)


class BioCell:
    def __init__(
        self,
        *,
        identity: CellIdentity,
        genome: Genome,
        nucleus: Nucleus,
        membrane: Membrane,
        mitochondria: Mitochondria,
        ribosome: Ribosome,
        lysosome: Lysosome,
        checkpoints: CheckpointSuite,
        audit: AuditLedger,
    ) -> None:
        self.identity = identity
        self.genome = genome
        self.nucleus = nucleus
        self.membrane = membrane
        self.mitochondria = mitochondria
        self.ribosome = ribosome
        self.lysosome = lysosome
        self.checkpoints = checkpoints
        self.audit = audit
        self.phase = LifecyclePhase.G0
        self.active = True

    @classmethod
    def bootstrap(cls, *, role: CellRole) -> "BioCell":
        genome = Genome(
            {
                "genome_id": "genome_base_v0_1",
                "version": "0.1.0",
                "allowed_roles": [role.value],
                "allowed_paths": ["./sandbox"],
                "budgets": {"max_runtime_seconds": 30, "max_memory_mb": 256},
            }
        )
        snapshot = genome.snapshot()
        nucleus = Nucleus(allowed_actions={"execute_job", "mitosis"}, permission_profile="sandbox_worker")
        identity = nucleus.assign_identity(
            genome_hash=snapshot.genome_hash,
            snapshot_id=snapshot.snapshot_id,
            role=role,
        )
        audit = AuditLedger(cell_id=identity.cell_id)
        cell = cls(
            identity=identity,
            genome=genome,
            nucleus=nucleus,
            membrane=Membrane(
                allowed_input_keys={"job_id", "type", "value", "required_runtime_seconds", "required_memory_mb"},
                allowed_output_keys={"result"},
            ),
            mitochondria=Mitochondria(max_runtime_seconds=30, max_memory_mb=256),
            ribosome=Ribosome(allowed_job_types={"echo"}),
            lysosome=Lysosome(destructive_delete=False),
            checkpoints=CheckpointSuite(min_health_score=0.8),
            audit=audit,
        )
        audit.record(
            event_type="cell_bootstrapped",
            lifecycle_phase=cell.phase,
            reason="root cell created",
            metadata={"role": role.value},
        )
        return cell

    @property
    def audit_events(self):
        return self.audit.events

    def run_job(self, payload: dict[str, object]) -> JobResult:
        if not self.active:
            result = JobResult(str(payload.get("job_id", "unknown")), False, {}, "cell is not active")
            self.audit.record(
                event_type="job_rejected",
                lifecycle_phase=self.phase,
                reason=result.reason,
                metadata={"job_id": result.job_id},
            )
            return result

        validation = self.membrane.validate_input(payload)
        if not validation.valid:
            result = JobResult(str(payload.get("job_id", "unknown")), False, {}, validation.reason)
            self.audit.record(
                event_type="job_rejected",
                lifecycle_phase=self.phase,
                reason=validation.reason,
                metadata={"job_id": result.job_id},
            )
            return result

        request = BudgetRequest(
            runtime_seconds=float(payload.get("required_runtime_seconds", 1.0)),
            memory_mb=float(payload.get("required_memory_mb", 1.0)),
        )
        reservation = self.mitochondria.reserve(request)
        if not reservation.accepted:
            result = JobResult(str(payload["job_id"]), False, {}, reservation.reason)
            self.audit.record(
                event_type="job_rejected",
                lifecycle_phase=self.phase,
                reason=reservation.reason,
                metadata={"job_id": result.job_id},
            )
            return result

        job = Job(
            job_id=str(payload["job_id"]),
            payload=payload,
            required_runtime_seconds=request.runtime_seconds,
            required_memory_mb=request.memory_mb,
        )
        result = self.ribosome.execute(job)
        self.audit.record(
            event_type="job_completed" if result.succeeded else "job_failed",
            lifecycle_phase=self.phase,
            reason=result.reason,
            metadata={"job_id": result.job_id},
        )
        return result

    def apoptose(self, reason: str) -> dict[str, object]:
        self.active = False
        self.phase = LifecyclePhase.APOPTOTIC
        self.audit.record(
            event_type="cell_apoptosis",
            lifecycle_phase=self.phase,
            reason=reason,
        )
        return {"phase": self.phase, "reason": reason}
