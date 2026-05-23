# BioClaw Growth Cycle Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic growth-cycle runner that composes expression, bacteria injection, immune inspection, turn closure, generation review, and organism growth.

**Architecture:** Keep `ExpressionEngine`, `ImmuneSystem`, `TurnEngine`, `GenerationEngine`, and `ProductOrganism` separate. Add `GrowthCycleRunner` as a small orchestrator, and tighten generation review so infected plasmid fixtures are quarantined without being promoted as stable growth.

**Tech Stack:** Python 3.12, dataclasses, enums, pytest, existing BioComponent YAML registry.

---

## File Structure

- Create `bioscaffold/growth.py`: growth-cycle orchestration and immutable result record.
- Modify `bioscaffold/immune.py`: preserve quarantined target refs and derive known markers from antibody memory.
- Modify `bioscaffold/generations.py`: remove quarantined and non-promotable pathogen structures from promotions.
- Modify `bioscaffold/__init__.py`: export growth runner types.
- Modify `tests/test_component_cards.py`: add growth-cycle card and public exports.
- Modify `tests/test_generations.py`: add pathogen promotion/quarantine regression.
- Modify `tests/test_molecules_immune.py`: add immune-memory learning regression.
- Create `tests/test_growth.py`: full clean and infected growth-cycle tests.
- Create `bio_components/processes/growth-cycle.yaml`: card for the orchestrated cycle.

## Task 1: Growth Cycle Card

**Files:**
- Modify: `tests/test_component_cards.py`
- Create: `bio_components/processes/growth-cycle.yaml`

- [x] **Step 1: Write failing card expectation**

Add `"growth-cycle"` to the expected card-name set in `tests/test_component_cards.py`.

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_component_cards.py::test_all_repository_cards_are_valid -v`

Expected: FAIL because `growth-cycle` is missing.

- [x] **Step 3: Add card**

Create `bio_components/processes/growth-cycle.yaml`:

```yaml
bio_component:
  name: growth-cycle
  scale: organism
  biological_role: Coordinates repeated biological processes that produce stable growth.
  software_role: Runs one deterministic product growth cycle from gene expression through generation review and organism integration.
  implementation_status: planned
  inputs: [product_organism, molecule_registry, gene, promoter, pathogen_fixtures]
  outputs: [closed_turn, reviewed_generation, updated_product_organism]
  internal_state:
    cycle_refs: Turn, generation, and organism identifiers for one synchronized cycle.
  sensors: [terminal_task_count, immune_event_count, quarantined_structure_count]
  control_rules: [A growth cycle must close the turn before reviewing the generation.]
  repair_rules: [Blocked expression remains terminal evidence for the next cycle.]
  recycle_rules: [Quarantined fixtures are preserved for immune memory and later archive.]
  replication_rules: [Growth cycles do not create additional active organisms.]
  failure_modes: [open turn reviewed, pathogen promoted as stable growth, cross-organism generation]
  safety_limits:
    autonomous_deployment: false
    live_malware: false
    multiple_active_organisms: false
  tests_required: [test_growth_cycle_injects_bacteria_and_quarantines_with_immune_memory]
  shutdown_condition: Growth cycle cannot produce a closed turn.
  human_review_required: true
```

- [x] **Step 4: Run card tests**

Run: `python -m pytest tests/test_component_cards.py tests/test_card_registry.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_component_cards.py bio_components/processes/growth-cycle.yaml
git commit -m "Add growth cycle component card"
```

## Task 2: Generation Review Hardening

**Files:**
- Modify: `tests/test_generations.py`
- Modify: `bioscaffold/immune.py`
- Modify: `bioscaffold/generations.py`

- [x] **Step 1: Write failing generation hardening test**

Append to `tests/test_generations.py`:

```python
from bioscaffold.immune import ImmuneSystem, PathogenFixture


def test_generation_review_quarantines_pathogen_target_without_promoting_plasmid():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )
    injection_task = fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    immune_task, _event = ImmuneSystem(known_markers={"fake_completion_marker"}).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v1",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(injection_task, immune_task),
        )
    )

    reviewed = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        registry,
    )

    assert "plasmid.injected.fake_done.v1" in reviewed.quarantined_structures
    assert "plasmid.injected.fake_done.v1" not in reviewed.promoted_structures
    assert reviewed.immune_memory == ("antibody.fake_completion_marker",)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_generations.py::test_generation_review_quarantines_pathogen_target_without_promoting_plasmid -v`

Expected: FAIL because the immune task currently outputs the antibody ref and generation review promotes the injected plasmid.

- [x] **Step 3: Preserve quarantined target refs**

In `bioscaffold/immune.py`, change the quarantined task output from the antibody ref to the target ref and store the antibody in metadata:

```python
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
```

- [x] **Step 4: Prevent pathogen promotion**

In `bioscaffold/generations.py`, filter promotions after quarantine collection:

```python
        quarantined_refs = set(quarantined)
        promoted = [
            ref
            for ref in promoted
            if ref not in quarantined_refs and self._is_promotable(registry, ref)
        ]
```

Add this helper to `GenerationEngine`:

```python
    def _is_promotable(self, registry: MoleculeRegistry, ref: str) -> bool:
        try:
            structure = registry.get(ref)
        except KeyError:
            return True
        if structure.molecule_type in {MoleculeType.PLASMID, MoleculeType.ANTIGEN}:
            return False
        if "pathogen_fixture" in structure.markers:
            return False
        return True
```

- [x] **Step 5: Run generation tests**

Run: `python -m pytest tests/test_generations.py tests/test_molecules_immune.py -v`

Expected: PASS.

- [x] **Step 6: Commit**

```powershell
git add tests/test_generations.py bioscaffold/immune.py bioscaffold/generations.py
git commit -m "Harden generation review against pathogen promotion"
```

## Task 3: Immune Memory Learning

**Files:**
- Modify: `tests/test_molecules_immune.py`
- Modify: `bioscaffold/immune.py`

- [x] **Step 1: Write failing immune memory test**

Append to `tests/test_molecules_immune.py`:

```python
def test_immune_system_learns_known_markers_from_antibody_memory():
    registry = MoleculeRegistry()
    first_fixture = PathogenFixture(
        fixture_id="bacteria_fake_done_v1",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )
    second_fixture = PathogenFixture(
        fixture_id="bacteria_fake_done_v2",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v2",
        payload="fake done marker repeat",
    )
    first_fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    ImmuneSystem(known_markers={"fake_completion_marker"}).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v1",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    second_fixture.inject(
        registry,
        turn_id="turn_000002",
        generation_id="gen_000002",
        organism_id="organism_000001",
    )

    task, event = ImmuneSystem.from_registry(registry).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v2",
        turn_id="turn_000002",
        generation_id="gen_000002",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.QUARANTINED
    assert event.antibody_ref == "antibody.fake_completion_marker"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_molecules_immune.py::test_immune_system_learns_known_markers_from_antibody_memory -v`

Expected: FAIL because `ImmuneSystem.from_registry` does not exist.

- [x] **Step 3: Implement memory loading**

Add this classmethod to `ImmuneSystem` in `bioscaffold/immune.py`:

```python
    @classmethod
    def from_registry(cls, registry: MoleculeRegistry) -> "ImmuneSystem":
        markers: set[str] = set()
        for antibody in registry.find_by_type(MoleculeType.ANTIBODY):
            markers.update(antibody.markers)
        return cls(known_markers=markers)
```

- [x] **Step 4: Run immune tests**

Run: `python -m pytest tests/test_molecules_immune.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_molecules_immune.py bioscaffold/immune.py
git commit -m "Add immune memory loading"
```

## Task 4: Growth Cycle Runner

**Files:**
- Create: `tests/test_growth.py`
- Create: `bioscaffold/growth.py`

- [x] **Step 1: Write failing growth runner tests**

Create `tests/test_growth.py`:

```python
from bioscaffold.growth import GrowthCycleRunner
from bioscaffold.immune import ImmuneSystem, PathogenFixture
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.organism import OrganismStatus, ProductOrganism
from bioscaffold.turns import TurnStatus
from bioscaffold.generations import GenerationStatus


def seed_expression_registry() -> MoleculeRegistry:
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
            source_refs=("dna.product_blueprint",),
            markers=("auth",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.auth.password_policy",
            molecule_type=MoleculeType.PROMOTER,
            content="Activate password policy work.",
            source_refs=("gene.auth.password_policy",),
            markers=("active",),
        )
    )
    return registry


def test_growth_cycle_runs_expression_and_clean_delivery_path():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=organism,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
    )
    archived = result.organism.deliver().archive()

    assert result.turn.status is TurnStatus.CLOSED
    assert result.generation.status is GenerationStatus.REVIEWED
    assert "protein.auth.password_policy.v1" in result.generation.promoted_structures
    assert result.organism.status is OrganismStatus.GROWING
    assert archived.status is OrganismStatus.ARCHIVED


def test_growth_cycle_injects_bacteria_and_quarantines_with_immune_memory():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=organism,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
        pathogen_fixtures=(fixture,),
    )

    assert result.organism.status is OrganismStatus.QUARANTINED
    assert "protein.auth.password_policy.v1" in result.generation.promoted_structures
    assert "plasmid.injected.fake_done.v1" in result.generation.quarantined_structures
    assert "plasmid.injected.fake_done.v1" not in result.generation.promoted_structures
    assert result.generation.immune_memory == ("antibody.fake_completion_marker",)
    assert result.turn.immune_events == ("immune.quarantine.plasmid.injected.fake_done.v1",)
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_growth.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.growth'`.

- [x] **Step 3: Implement growth runner**

Create `bioscaffold/growth.py`:

```python
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
    ) -> GrowthCycleResult:
        tasks: list[MicroTask] = []
        immune_events: list[ImmuneEvent] = []
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
        for fixture in pathogen_fixtures:
            injection_task = fixture.inject(
                registry,
                turn_id=turn_id,
                generation_id=generation_id,
                organism_id=organism.organism_id,
            )
            tasks.append(injection_task)
            if injection_task.outputs:
                immune_task, event = inspector.inspect(
                    registry,
                    target_ref=injection_task.outputs[0],
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
```

- [x] **Step 4: Run growth tests**

Run: `python -m pytest tests/test_growth.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_growth.py bioscaffold/growth.py
git commit -m "Add growth cycle runner"
```

## Task 5: Public Exports And Full Verification

**Files:**
- Modify: `tests/test_component_cards.py`
- Modify: `bioscaffold/__init__.py`

- [x] **Step 1: Write failing public export expectation**

Add `"GrowthCycleResult"` and `"GrowthCycleRunner"` to the `bioscaffold.__all__` expectation in `tests/test_component_cards.py`.

- [x] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_component_cards.py::test_package_imports -v`

Expected: FAIL because growth-cycle exports are not present.

- [x] **Step 3: Update public exports**

Import and export `GrowthCycleResult` and `GrowthCycleRunner` in `bioscaffold/__init__.py`.

- [x] **Step 4: Run full verification**

Run: `python -m pytest -v`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit code 0.

- [x] **Step 5: Commit**

```powershell
git add bioscaffold/__init__.py tests/test_component_cards.py
git commit -m "Export growth cycle runner"
```

## Self-Review

Spec coverage:

- Turn/generation composition: Task 4 runs expression, immune inspection, turn closure, generation review, and organism integration.
- Immune hardening: Tasks 2 and 3 preserve quarantined targets and load known markers from antibody memory.
- Bacteria safety: Task 2 prevents inert pathogen fixtures from being promoted as stable product growth.
- Single active organism: Task 4 integrates a reviewed generation into the provided `ProductOrganism` only.

Placeholder scan:

- No placeholder text is left in required steps.
- Every code task includes a failing test, expected failure, implementation, verification, and commit.

Type consistency:

- `GrowthCycleRunner`, `GrowthCycleResult`, `ImmuneSystem.from_registry`, `GenerationEngine.review`, and `ProductOrganism.integrate_generation` are consistently named across tests and implementation snippets.
