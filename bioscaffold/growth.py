from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.expression import ExpressionEngine
from bioscaffold.generations import Generation, GenerationEngine
from bioscaffold.immune import ImmuneEvent, ImmuneSystem, PathogenFixture
from bioscaffold.microtasks import MicroTask, TaskState
from bioscaffold.molecules import MoleculeRegistry
from bioscaffold.organism import ProductOrganism
from bioscaffold.turns import Turn, TurnEngine


@dataclass(frozen=True)
class GrowthCycleResult:
    registry: MoleculeRegistry
    turn: Turn
    generation: Generation
    organism: ProductOrganism
    immune_events: tuple[ImmuneEvent, ...] = ()


class GrowthCycleRunner:
    def __init__(
        self,
        *,
        expression_engine: ExpressionEngine | None = None,
        turn_engine: TurnEngine | None = None,
        generation_engine: GenerationEngine | None = None,
    ) -> None:
        self.expression_engine = expression_engine or ExpressionEngine()
        self.turn_engine = turn_engine or TurnEngine()
        self.generation_engine = generation_engine or GenerationEngine()

    def run_generation(
        self,
        *,
        registry: MoleculeRegistry,
        organism: ProductOrganism,
        gene_ref: str,
        promoter_ref: str,
        generation_id: str,
        turn_id: str,
        immune_system: ImmuneSystem | None = None,
        pathogen_fixtures: tuple[PathogenFixture, ...] = (),
        prefix_tasks: tuple[MicroTask, ...] = (),
    ) -> GrowthCycleResult:
        tasks: list[MicroTask] = list(prefix_tasks)
        immune_events: list[ImmuneEvent] = []
        if all(task.state is TaskState.COMPLETE for task in prefix_tasks):
            transcribe_task = self.expression_engine.transcribe(
                registry,
                gene_ref=gene_ref,
                promoter_ref=promoter_ref,
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism.organism_id,
            )
            tasks.append(transcribe_task)
            if transcribe_task.state is TaskState.COMPLETE:
                splice_task = self.expression_engine.splice(
                    registry,
                    transcript_ref=transcribe_task.outputs[0],
                    turn_id=turn_id,
                    generation_id=generation_id,
                    organism_id=organism.organism_id,
                )
                tasks.append(splice_task)
                if splice_task.state is TaskState.COMPLETE:
                    tasks.append(
                        self.expression_engine.translate(
                            registry,
                            spliced_ref=splice_task.outputs[0],
                            turn_id=turn_id,
                            generation_id=generation_id,
                            organism_id=organism.organism_id,
                        )
                    )

        inspector = immune_system or ImmuneSystem.from_registry(registry)
        inspected_refs: set[str] = set()
        for fixture in pathogen_fixtures:
            injection_task = fixture.inject(
                registry,
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism.organism_id,
            )
            tasks.append(injection_task)
            if injection_task.outputs:
                inspected_refs.add(injection_task.outputs[0])
                immune_task, event = inspector.inspect(
                    registry,
                    target_ref=injection_task.outputs[0],
                    turn_id=turn_id,
                    generation_id=generation_id,
                    organism_id=organism.organism_id,
                )
                tasks.append(immune_task)
                immune_events.append(event)

        for target_ref in self._completed_output_refs(tasks):
            if target_ref in inspected_refs:
                continue
            try:
                registry.get(target_ref)
            except KeyError:
                continue
            inspected_refs.add(target_ref)
            immune_task, event = inspector.inspect(
                registry,
                target_ref=target_ref,
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism.organism_id,
            )
            tasks.append(immune_task)
            immune_events.append(event)

        turn = self.turn_engine.close(
            Turn(
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism.organism_id,
                tasks=tuple(tasks),
                immune_events=tuple(event.event_id for event in immune_events),
            )
        )
        generation = self.generation_engine.review(
            Generation(
                generation_id=generation_id,
                organism_id=organism.organism_id,
                turns=(turn,),
            ),
            registry,
        )
        return GrowthCycleResult(
            registry=registry,
            turn=turn,
            generation=generation,
            organism=organism.integrate_generation(generation),
            immune_events=tuple(immune_events),
        )

    def _completed_output_refs(self, tasks: list[MicroTask]) -> tuple[str, ...]:
        refs = []
        for task in tuple(tasks):
            if task.state is not TaskState.COMPLETE:
                continue
            refs.extend(task.outputs)
        return tuple(dict.fromkeys(refs))
