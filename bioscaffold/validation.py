from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


DEFAULT_INVALID_MARKERS = frozenset(
    {
        "audit_tamper",
        "fake_completion_marker",
        "invalid_lineage",
        "malformed",
    }
)


@dataclass(frozen=True)
class ArtifactValidationResult:
    tasks: tuple[MicroTask, ...]
    validated_refs: tuple[str, ...]
    quarantined_refs: tuple[str, ...]
    antibody_refs: tuple[str, ...]


class ArtifactValidationEngine:
    def __init__(self, *, invalid_markers: set[str] | frozenset[str] | None = None) -> None:
        self.invalid_markers = frozenset(invalid_markers or DEFAULT_INVALID_MARKERS)

    def validate_all(
        self,
        registry: MoleculeRegistry,
        *,
        artifact_refs: tuple[str, ...],
        organism_id: str,
        generation_id: str,
        turn_id: str,
    ) -> ArtifactValidationResult:
        tasks: list[MicroTask] = []
        validated_refs: list[str] = []
        quarantined_refs: list[str] = []
        antibody_refs: list[str] = []
        for artifact_ref in artifact_refs:
            task = self._task(
                artifact_ref,
                organism_id=organism_id,
                generation_id=generation_id,
                turn_id=turn_id,
            )
            try:
                artifact = registry.get(artifact_ref)
            except KeyError:
                tasks.append(
                    task.with_terminal(
                        TaskState.BLOCKED,
                        reason=f"missing artifact for validation: {artifact_ref}",
                    )
                )
                continue
            if artifact.molecule_type is not MoleculeType.PROTEIN:
                tasks.append(
                    task.with_terminal(
                        TaskState.FAILED,
                        reason=f"{artifact_ref} is not a protein artifact",
                    )
                )
                continue

            invalid_marker = self._first_invalid_marker(artifact.markers)
            if invalid_marker is None:
                validated_refs.append(artifact_ref)
                tasks.append(
                    task.with_terminal(
                        TaskState.COMPLETE,
                        reason="artifact validated",
                        outputs=(artifact_ref,),
                    )
                )
                continue

            antibody_ref = self._record_antibody(registry, artifact, invalid_marker)
            quarantined_refs.append(artifact_ref)
            antibody_refs.append(antibody_ref)
            tasks.append(
                task.with_terminal(
                    TaskState.QUARANTINED,
                    reason=f"invalid artifact marker detected: {invalid_marker}",
                    outputs=(artifact_ref,),
                    metadata={"antibody_ref": antibody_ref, "invalid_marker": invalid_marker},
                )
            )

        return ArtifactValidationResult(
            tasks=tuple(tasks),
            validated_refs=tuple(dict.fromkeys(validated_refs)),
            quarantined_refs=tuple(dict.fromkeys(quarantined_refs)),
            antibody_refs=tuple(dict.fromkeys(antibody_refs)),
        )

    def _task(
        self,
        artifact_ref: str,
        *,
        organism_id: str,
        generation_id: str,
        turn_id: str,
    ) -> MicroTask:
        return MicroTask(
            task_id=f"task.validate.{artifact_ref}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.PROTEIN,
            operation=MicroOperation.VALIDATE,
            target_ref=artifact_ref,
            agent_hat=AgentHat.VALIDATOR,
            expected_output="validated_artifact",
            metadata={"project_workflow": True, "workflow_phase": "validation"},
        )

    def _first_invalid_marker(self, markers: tuple[str, ...]) -> str | None:
        detected = sorted(set(markers).intersection(self.invalid_markers))
        if not detected:
            return None
        return detected[0]

    def _record_antibody(
        self,
        registry: MoleculeRegistry,
        artifact: MolecularStructure,
        marker: str,
    ) -> str:
        antibody_ref = f"antibody.{marker}"
        try:
            registry.add(
                MolecularStructure(
                    ref=antibody_ref,
                    molecule_type=MoleculeType.ANTIBODY,
                    content=f"signature for invalid artifact marker: {marker}",
                    source_refs=(artifact.ref,),
                    markers=(marker,),
                )
            )
        except ValueError as exc:
            if "duplicate molecular structure ref" not in str(exc):
                raise
        return antibody_ref
