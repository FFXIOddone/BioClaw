from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


@dataclass(frozen=True)
class ImmuneEvent:
    event_id: str
    target_ref: str
    marker: str
    action: str
    antibody_ref: str
    reason: str


@dataclass(frozen=True)
class PathogenFixture:
    fixture_id: str
    defect_marker: str
    injected_ref: str
    payload: str

    def inject(
        self,
        registry: MoleculeRegistry,
        *,
        turn_id: str,
        generation_id: str,
        organism_id: str,
    ) -> MicroTask:
        registry.add(
            MolecularStructure(
                ref=self.injected_ref,
                molecule_type=MoleculeType.PLASMID,
                content=self.payload,
                markers=(self.defect_marker, "pathogen_fixture"),
                metadata={"fixture_id": self.fixture_id, "inert": True},
            )
        )
        return MicroTask(
            task_id=f"task.inject.{self.fixture_id}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.MOLECULAR,
            operation=MicroOperation.INJECT,
            target_ref=self.injected_ref,
            agent_hat=AgentHat.BACTERIA,
            expected_output="inert_plasmid",
        ).with_terminal(
            TaskState.COMPLETE,
            reason="inert pathogen fixture injected",
            outputs=(self.injected_ref,),
        )


class ImmuneSystem:
    def __init__(self, *, known_markers: set[str]) -> None:
        self.known_markers = set(known_markers)

    @classmethod
    def from_registry(cls, registry: MoleculeRegistry) -> "ImmuneSystem":
        markers: set[str] = set()
        for antibody in registry.find_by_type(MoleculeType.ANTIBODY):
            markers.update(antibody.markers)
        return cls(known_markers=markers)

    def inspect(
        self,
        registry: MoleculeRegistry,
        *,
        target_ref: str,
        turn_id: str,
        generation_id: str,
        organism_id: str,
    ) -> tuple[MicroTask, ImmuneEvent]:
        target = registry.get(target_ref)
        detected = sorted(set(target.markers).intersection(self.known_markers))
        if not detected:
            event = ImmuneEvent(
                event_id=f"immune.clean.{target_ref}",
                target_ref=target_ref,
                marker="",
                action="clear",
                antibody_ref="",
                reason="no known immune marker detected",
            )
            task = MicroTask(
                task_id=f"task.detect.{target_ref}",
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism_id,
                scale=BioScale.MOLECULAR,
                operation=MicroOperation.DETECT,
                target_ref=target_ref,
                agent_hat=AgentHat.WHITE_BLOOD_CELL,
                expected_output="immune_event",
            ).with_terminal(TaskState.COMPLETE, reason=event.reason)
            return task, event

        marker = detected[0]
        antibody_ref = f"antibody.{marker}"
        try:
            registry.add(
                MolecularStructure(
                    ref=antibody_ref,
                    molecule_type=MoleculeType.ANTIBODY,
                    content=f"signature for {marker}",
                    source_refs=(target_ref,),
                    markers=(marker,),
                )
            )
        except ValueError:
            pass
        event = ImmuneEvent(
            event_id=f"immune.quarantine.{target_ref}",
            target_ref=target_ref,
            marker=marker,
            action="quarantine",
            antibody_ref=antibody_ref,
            reason=f"known immune marker detected: {marker}",
        )
        task = MicroTask(
            task_id=f"task.detect.{target_ref}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.MOLECULAR,
            operation=MicroOperation.DETECT,
            target_ref=target_ref,
            agent_hat=AgentHat.WHITE_BLOOD_CELL,
            expected_output="immune_event",
        ).with_terminal(
            TaskState.QUARANTINED,
            reason=event.reason,
            outputs=(target_ref,),
            metadata={"immune_event_id": event.event_id, "antibody_ref": antibody_ref},
        )
        return task, event
