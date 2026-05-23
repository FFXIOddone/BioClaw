# BioClaw Turn Generation Microtask Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first deterministic turn/generation engine where tiny DNA/RNA-level micro-tasks compose upward and immune fixtures harden the product organism.

**Architecture:** Add small focused modules under `bioscaffold/`: task contracts in `microtasks.py`, synchronized turn barriers in `turns.py`, molecular structures in `molecules.py`, safe bacteria/white-blood-cell hardening in `immune.py`, and generation review in `generations.py`. Each module is tested independently before integration.

**Tech Stack:** Python 3.12, dataclasses, enums, Pydantic/YAML card validation already present, pytest.

---

## File Structure

- Create `bioscaffold/microtasks.py`: enums and immutable task records for scale, operation, agent hat, terminal state, and hat policy.
- Create `bioscaffold/turns.py`: `Turn`, `TurnStatus`, and `TurnEngine` with the strict terminal-state barrier.
- Create `bioscaffold/molecules.py`: DNA/RNA-level molecule records and in-memory registry.
- Create `bioscaffold/immune.py`: deterministic bacteria fixtures, white-blood-cell inspection, immune events, and antibody memory.
- Create `bioscaffold/generations.py`: `Generation`, `GenerationStatus`, and `GenerationEngine` that reviews closed turns only.
- Modify `bioscaffold/__init__.py`: export the core public types.
- Create `tests/test_microtasks.py`: micro-task and hat-policy behavior.
- Create `tests/test_turns.py`: turn barrier behavior.
- Create `tests/test_molecules_immune.py`: molecule registry and immune fixture behavior.
- Create `tests/test_generations.py`: generation review and promotion behavior.
- Modify `tests/test_component_cards.py`: include the new molecular/process cards in registry expectations.
- Create molecular cards under `bio_components/molecules/`.
- Create process cards under `bio_components/processes/`.

## Task 1: BioComponent Cards For Molecular And Immune Layer

**Files:**
- Modify: `tests/test_component_cards.py`
- Create: `bio_components/molecules/dna.yaml`
- Create: `bio_components/molecules/gene.yaml`
- Create: `bio_components/molecules/rna-transcript.yaml`
- Create: `bio_components/molecules/plasmid.yaml`
- Create: `bio_components/molecules/antigen.yaml`
- Create: `bio_components/molecules/antibody.yaml`
- Create: `bio_components/processes/transcription.yaml`
- Create: `bio_components/processes/splicing.yaml`
- Create: `bio_components/processes/immune-response.yaml`

- [x] **Step 1: Write the failing registry expectation**

Replace the `names == {...}` assertion in `tests/test_component_cards.py` with this set:

```python
    assert names == {
        "antibody",
        "antigen",
        "apoptosis",
        "autophagy",
        "cytoskeleton",
        "dna",
        "endoplasmic-reticulum",
        "gene",
        "golgi-apparatus",
        "immune-response",
        "lysosome",
        "meiosis",
        "mitochondria",
        "mitosis",
        "nucleus",
        "plasma-membrane",
        "plasmid",
        "ribosome",
        "rna-transcript",
        "splicing",
        "transcription",
    }
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_component_cards.py::test_all_repository_cards_are_valid -v`

Expected: FAIL because the new card names are missing.

- [x] **Step 3: Add molecular and immune cards**

Create `bio_components/molecules/dna.yaml`:

```yaml
bio_component:
  name: dna
  scale: molecular
  biological_role: Stores durable inherited instructions.
  software_role: Stores durable product blueprint, constraints, and inherited decisions.
  implementation_status: planned
  inputs: [product_intent, constraints]
  outputs: [genes, promoters]
  internal_state:
    sequence: Ordered instruction records and checksums.
  sensors: [checksum_status]
  control_rules: [DNA records are durable and cannot be silently mutated.]
  repair_rules: [Invalid DNA records become repair proposals.]
  recycle_rules: [Superseded DNA records are archived with lineage metadata.]
  replication_rules: [DNA can be copied only into an explicit transcript or snapshot.]
  failure_modes: [silent mutation, missing lineage, invalid checksum]
  safety_limits:
    production_access: false
    silent_mutation: false
  tests_required: [test_molecule_registry_stores_and_finds_structures]
  shutdown_condition: DNA checksum or lineage becomes contradictory.
  human_review_required: true
```

Create `bio_components/molecules/gene.yaml`:

```yaml
bio_component:
  name: gene
  scale: molecular
  biological_role: Encodes one heritable functional instruction.
  software_role: Represents one requirement, capability, quality rule, constraint, or delivery rule.
  implementation_status: planned
  inputs: [dna]
  outputs: [rna_transcript]
  internal_state:
    gene_ref: Stable product-work instruction reference.
  sensors: [activation_status, contradiction_markers]
  control_rules: [A gene must pass promoter checks before transcription.]
  repair_rules: [Contradictory genes are quarantined for review.]
  recycle_rules: [Rejected genes are archived as design evidence.]
  replication_rules: [Gene copies must preserve source DNA reference.]
  failure_modes: [contradictory requirement, missing source reference]
  safety_limits:
    autonomous_execution: false
  tests_required: [test_generation_review_promotes_only_closed_turn_outputs]
  shutdown_condition: Gene source cannot be traced.
  human_review_required: true
```

Create `bio_components/molecules/rna-transcript.yaml`:

```yaml
bio_component:
  name: rna-transcript
  scale: molecular
  biological_role: Carries copied genetic instructions for expression.
  software_role: Active micro-task work order derived from a gene.
  implementation_status: planned
  inputs: [gene, promoter]
  outputs: [artifact_fragment_task]
  internal_state:
    transcript_ref: Stable work-order reference.
  sensors: [splice_status, immune_markers]
  control_rules: [A transcript must be spliced and validated before translation.]
  repair_rules: [Malformed transcripts are quarantined.]
  recycle_rules: [Failed transcripts are archived with failure reason.]
  replication_rules: [Transcript copies must preserve source gene reference.]
  failure_modes: [malformed transcript, inactive clause, hostile marker]
  safety_limits:
    direct_file_write: false
  tests_required: [test_pathogen_fixture_injects_inert_plasmid]
  shutdown_condition: Transcript carries hostile or contradictory markers.
  human_review_required: true
```

Create `bio_components/molecules/plasmid.yaml`:

```yaml
bio_component:
  name: plasmid
  scale: molecular
  biological_role: Carries extra genetic material outside the primary chromosome.
  software_role: Injected external instruction bundle used by deterministic bacteria fixtures.
  implementation_status: planned
  inputs: [pathogen_fixture]
  outputs: [defect_marker]
  internal_state:
    plasmid_ref: Stable injected fixture reference.
  sensors: [defect_markers]
  control_rules: [Plasmids are inert test data and cannot execute.]
  repair_rules: [Unsafe plasmids are quarantined and fingerprinted.]
  recycle_rules: [Quarantined plasmids are archived as immune evidence.]
  replication_rules: [Plasmids do not replicate in the simulator.]
  failure_modes: [fake completion marker, invalid lineage marker]
  safety_limits:
    executable: false
    network_access: false
  tests_required: [test_pathogen_fixture_injects_inert_plasmid]
  shutdown_condition: Plasmid attempts to act outside fixture data.
  human_review_required: true
```

Create `bio_components/molecules/antigen.yaml`:

```yaml
bio_component:
  name: antigen
  scale: molecular
  biological_role: Marker recognized by immune response.
  software_role: Marker that identifies a defect, contradiction, or hostile pattern.
  implementation_status: planned
  inputs: [structure_markers]
  outputs: [immune_detection]
  internal_state:
    marker: Stable defect signature.
  sensors: [marker_frequency]
  control_rules: [Antigens are evidence markers, not executable behavior.]
  repair_rules: [Unknown antigens are preserved for review.]
  recycle_rules: [Resolved antigens are archived with antibody references.]
  replication_rules: [Antigen records can be copied into immune memory.]
  failure_modes: [false positive marker, missing evidence source]
  safety_limits:
    executable: false
  tests_required: [test_white_blood_cell_quarantines_known_marker]
  shutdown_condition: Antigen lacks a source structure.
  human_review_required: true
```

Create `bio_components/molecules/antibody.yaml`:

```yaml
bio_component:
  name: antibody
  scale: molecular
  biological_role: Binds to known antigens for immune response.
  software_role: Learned regression signature or response rule.
  implementation_status: planned
  inputs: [antigen, immune_event]
  outputs: [immune_memory]
  internal_state:
    signature: Stable learned defect signature.
  sensors: [reuse_count]
  control_rules: [Antibodies can block future matching defects earlier.]
  repair_rules: [Overbroad antibodies are demoted to review.]
  recycle_rules: [Obsolete antibodies are archived with replacement reason.]
  replication_rules: [Antibody memory can seed later generations.]
  failure_modes: [overbroad block, missing immune evidence]
  safety_limits:
    autonomous_policy_mutation: false
  tests_required: [test_immune_memory_records_accepted_antibodies]
  shutdown_condition: Antibody has no antigen evidence.
  human_review_required: true
```

Create `bio_components/processes/transcription.yaml`:

```yaml
bio_component:
  name: transcription
  scale: molecular
  biological_role: Copies DNA instructions into RNA.
  software_role: Converts active genes into RNA micro-task work orders.
  implementation_status: planned
  inputs: [gene, promoter]
  outputs: [rna_transcript]
  internal_state:
    source_gene_ref: Gene being copied.
  sensors: [promoter_status]
  control_rules: [Only active genes can be transcribed.]
  repair_rules: [Inactive genes produce blocked tasks with evidence.]
  recycle_rules: [Failed transcripts are archived.]
  replication_rules: [Transcript must preserve source gene ref.]
  failure_modes: [inactive promoter, missing gene]
  safety_limits:
    direct_execution: false
  tests_required: [test_microtask_terminal_transition_records_outputs]
  shutdown_condition: Source gene cannot be validated.
  human_review_required: true
```

Create `bio_components/processes/splicing.yaml`:

```yaml
bio_component:
  name: splicing
  scale: molecular
  biological_role: Edits RNA before expression.
  software_role: Removes inactive or invalid clauses from a transcript before work execution.
  implementation_status: planned
  inputs: [rna_transcript]
  outputs: [spliced_transcript]
  internal_state:
    splice_rules: Clause removal evidence.
  sensors: [invalid_clause_count]
  control_rules: [Splicing must preserve source transcript lineage.]
  repair_rules: [Unspliceable transcripts are quarantined.]
  recycle_rules: [Removed clauses are archived as evidence.]
  replication_rules: [Spliced transcript must point to original transcript.]
  failure_modes: [lineage loss, invalid clause remains]
  safety_limits:
    destructive_edit: false
  tests_required: [test_agent_hat_policy_rejects_out_of_scope_operation]
  shutdown_condition: Splicing would remove lineage evidence.
  human_review_required: true
```

Create `bio_components/processes/immune-response.yaml`:

```yaml
bio_component:
  name: immune-response
  scale: molecular
  biological_role: Detects and responds to abnormal or hostile markers.
  software_role: Quarantines deterministic defect fixtures and records antibody memory.
  implementation_status: planned
  inputs: [antigen, molecule_registry]
  outputs: [immune_event, antibody]
  internal_state:
    known_markers: Markers the immune system can recognize.
  sensors: [detected_marker_count]
  control_rules: [Immune response cannot delete evidence.]
  repair_rules: [Unknown markers are preserved for generation review.]
  recycle_rules: [Resolved attacks are archived with immune event id.]
  replication_rules: [Accepted antibodies can seed later generations.]
  failure_modes: [missed known marker, evidence deletion]
  safety_limits:
    evidence_deletion: false
    live_malware: false
  tests_required: [test_white_blood_cell_quarantines_known_marker]
  shutdown_condition: Immune response attempts to hide evidence.
  human_review_required: true
```

- [x] **Step 4: Run card tests**

Run: `python -m pytest tests/test_component_cards.py tests/test_card_registry.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_component_cards.py bio_components/molecules bio_components/processes
git commit -m "Add molecular and immune component cards"
```

## Task 2: MicroTask Contracts And Hat Policy

**Files:**
- Create: `tests/test_microtasks.py`
- Create: `bioscaffold/microtasks.py`

- [x] **Step 1: Write failing micro-task tests**

Create `tests/test_microtasks.py`:

```python
import pytest

from bioscaffold.microtasks import (
    AgentHat,
    AgentHatPolicy,
    BioScale,
    MicroOperation,
    MicroTask,
    TaskState,
)


def test_microtask_terminal_transition_records_outputs():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
        inputs=("genome.product_requirements",),
        expected_output="located_gene_ref",
    )

    terminal = task.with_terminal(
        TaskState.COMPLETE,
        reason="gene located",
        outputs=("gene.auth.password_policy",),
    )

    assert terminal.is_terminal is True
    assert terminal.state is TaskState.COMPLETE
    assert terminal.reason == "gene located"
    assert terminal.outputs == ("gene.auth.password_policy",)


def test_microtask_rejects_non_terminal_transition():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    with pytest.raises(ValueError, match="state must be terminal"):
        task.with_terminal(TaskState.RUNNING, reason="still working")


def test_microtask_requires_terminal_reason():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    with pytest.raises(ValueError, match="terminal reason is required"):
        task.with_terminal(TaskState.FAILED, reason="")


def test_agent_hat_policy_allows_declared_operation():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.SPLICE,
        target_ref="transcript.auth.password_policy",
        agent_hat=AgentHat.SPLICER,
    )

    decision = AgentHatPolicy.default().authorize(task)

    assert decision.allowed is True


def test_agent_hat_policy_rejects_out_of_scope_operation():
    task = MicroTask(
        task_id="task_000001",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.INJECT,
        target_ref="transcript.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
    )

    decision = AgentHatPolicy.default().authorize(task)

    assert decision.allowed is False
    assert decision.reason == "hat gene_scout cannot perform inject"
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_microtasks.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.microtasks'`.

- [x] **Step 3: Implement micro-task contracts**

Create `bioscaffold/microtasks.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from bioscaffold.types import PolicyDecision


class BioScale(str, Enum):
    MOLECULAR = "molecular"
    PROTEIN = "protein"
    CELL = "cell"
    TISSUE = "tissue"
    ORGAN = "organ"
    ORGANISM = "organism"


class MicroOperation(str, Enum):
    FIND = "find"
    COPY = "copy"
    SPLICE = "splice"
    BIND = "bind"
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"
    PRODUCE = "produce"
    VALIDATE = "validate"
    INJECT = "inject"
    DETECT = "detect"
    QUARANTINE = "quarantine"
    NEUTRALIZE = "neutralize"
    RECORD = "record"
    PROMOTE = "promote"
    ARCHIVE = "archive"


class AgentHat(str, Enum):
    GENE_SCOUT = "gene_scout"
    SPLICER = "splicer"
    TRANSCRIBER = "transcriber"
    RIBOSOME_WORKER = "ribosome_worker"
    VALIDATOR = "validator"
    BACTERIA = "bacteria"
    WHITE_BLOOD_CELL = "white_blood_cell"
    MACROPHAGE = "macrophage"
    MEMORY_CELL = "memory_cell"
    GENERATION_REVIEWER = "generation_reviewer"


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"


TERMINAL_STATES = frozenset(
    {
        TaskState.COMPLETE,
        TaskState.FAILED,
        TaskState.BLOCKED,
        TaskState.QUARANTINED,
    }
)


@dataclass(frozen=True)
class MicroTask:
    task_id: str
    turn_id: str
    generation_id: str
    organism_id: str
    scale: BioScale
    operation: MicroOperation
    target_ref: str
    agent_hat: AgentHat
    inputs: tuple[str, ...] = ()
    expected_output: str = ""
    state: TaskState = TaskState.PENDING
    reason: str = ""
    outputs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def with_terminal(
        self,
        state: TaskState,
        *,
        reason: str,
        outputs: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> "MicroTask":
        if state not in TERMINAL_STATES:
            raise ValueError("state must be terminal")
        if not reason:
            raise ValueError("terminal reason is required")
        merged_metadata = dict(self.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return replace(
            self,
            state=state,
            reason=reason,
            outputs=tuple(outputs),
            metadata=merged_metadata,
        )


@dataclass(frozen=True)
class AgentHatPolicy:
    allowed_operations: dict[AgentHat, frozenset[MicroOperation]]

    @classmethod
    def default(cls) -> "AgentHatPolicy":
        return cls(
            allowed_operations={
                AgentHat.GENE_SCOUT: frozenset({MicroOperation.FIND, MicroOperation.RECORD}),
                AgentHat.SPLICER: frozenset({MicroOperation.SPLICE, MicroOperation.VALIDATE}),
                AgentHat.TRANSCRIBER: frozenset(
                    {MicroOperation.COPY, MicroOperation.TRANSCRIBE}
                ),
                AgentHat.RIBOSOME_WORKER: frozenset(
                    {MicroOperation.BIND, MicroOperation.TRANSLATE, MicroOperation.PRODUCE}
                ),
                AgentHat.VALIDATOR: frozenset(
                    {MicroOperation.VALIDATE, MicroOperation.RECORD}
                ),
                AgentHat.BACTERIA: frozenset({MicroOperation.INJECT, MicroOperation.RECORD}),
                AgentHat.WHITE_BLOOD_CELL: frozenset(
                    {
                        MicroOperation.DETECT,
                        MicroOperation.QUARANTINE,
                        MicroOperation.NEUTRALIZE,
                    }
                ),
                AgentHat.MACROPHAGE: frozenset(
                    {MicroOperation.QUARANTINE, MicroOperation.ARCHIVE}
                ),
                AgentHat.MEMORY_CELL: frozenset(
                    {MicroOperation.RECORD, MicroOperation.PROMOTE}
                ),
                AgentHat.GENERATION_REVIEWER: frozenset(
                    {MicroOperation.VALIDATE, MicroOperation.PROMOTE, MicroOperation.ARCHIVE}
                ),
            }
        )

    def authorize(self, task: MicroTask) -> PolicyDecision:
        allowed = self.allowed_operations.get(task.agent_hat, frozenset())
        if task.operation not in allowed:
            return PolicyDecision.deny(
                f"hat {task.agent_hat.value} cannot perform {task.operation.value}"
            )
        return PolicyDecision.allow("hat operation allowed")
```

- [x] **Step 4: Run micro-task tests**

Run: `python -m pytest tests/test_microtasks.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_microtasks.py bioscaffold/microtasks.py
git commit -m "Add microtask contracts and hat policy"
```

## Task 3: Strict Turn Barrier

**Files:**
- Create: `tests/test_turns.py`
- Create: `bioscaffold/turns.py`

- [x] **Step 1: Write failing turn tests**

Create `tests/test_turns.py`:

```python
import pytest

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.turns import Turn, TurnEngine, TurnStatus


def make_task(task_id: str, state: TaskState = TaskState.PENDING) -> MicroTask:
    task = MicroTask(
        task_id=task_id,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref=f"gene.{task_id}",
        agent_hat=AgentHat.GENE_SCOUT,
    )
    if state is TaskState.PENDING:
        return task
    return task.with_terminal(state, reason=f"{state.value} evidence", outputs=(f"output.{task_id}",))


def test_turn_cannot_close_with_non_terminal_tasks():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(make_task("task_000001"),),
    )

    with pytest.raises(ValueError, match="non-terminal tasks: task_000001"):
        TurnEngine().close(turn)


def test_turn_closes_when_all_tasks_are_terminal():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_000001", TaskState.COMPLETE),
            make_task("task_000002", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert closed.status is TurnStatus.CLOSED
    assert closed.terminal_counts == {
        "complete": 1,
        "failed": 0,
        "blocked": 0,
        "quarantined": 1,
    }
    assert closed.outputs == ("output.task_000001", "output.task_000002")


def test_turn_preserves_failed_blocked_and_quarantined_evidence():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_failed", TaskState.FAILED),
            make_task("task_blocked", TaskState.BLOCKED),
            make_task("task_quarantined", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert [task.reason for task in closed.tasks] == [
        "failed evidence",
        "blocked evidence",
        "quarantined evidence",
    ]
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_turns.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.turns'`.

- [x] **Step 3: Implement turn barrier**

Create `bioscaffold/turns.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.microtasks import MicroTask, TaskState


class TurnStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class Turn:
    turn_id: str
    generation_id: str
    organism_id: str
    tasks: tuple[MicroTask, ...] = ()
    status: TurnStatus = TurnStatus.OPEN
    outputs: tuple[str, ...] = ()
    immune_events: tuple[str, ...] = ()
    next_turn_proposals: tuple[str, ...] = ()

    @property
    def terminal_counts(self) -> dict[str, int]:
        return {
            TaskState.COMPLETE.value: sum(1 for task in self.tasks if task.state is TaskState.COMPLETE),
            TaskState.FAILED.value: sum(1 for task in self.tasks if task.state is TaskState.FAILED),
            TaskState.BLOCKED.value: sum(1 for task in self.tasks if task.state is TaskState.BLOCKED),
            TaskState.QUARANTINED.value: sum(
                1 for task in self.tasks if task.state is TaskState.QUARANTINED
            ),
        }


class TurnEngine:
    def close(self, turn: Turn) -> Turn:
        non_terminal = [task.task_id for task in turn.tasks if not task.is_terminal]
        if non_terminal:
            raise ValueError(f"turn cannot close with non-terminal tasks: {', '.join(non_terminal)}")
        outputs = tuple(output for task in turn.tasks for output in task.outputs)
        return replace(turn, status=TurnStatus.CLOSED, outputs=outputs)
```

- [x] **Step 4: Run turn tests**

Run: `python -m pytest tests/test_turns.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_turns.py bioscaffold/turns.py
git commit -m "Add strict turn barrier"
```

## Task 4: Molecule Registry

**Files:**
- Create: `tests/test_molecules_immune.py`
- Create: `bioscaffold/molecules.py`

- [x] **Step 1: Write failing molecule registry tests**

Create `tests/test_molecules_immune.py`:

```python
import pytest

from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


def test_molecule_registry_stores_and_finds_structures():
    registry = MoleculeRegistry()
    gene = MolecularStructure(
        ref="gene.auth.password_policy",
        molecule_type=MoleculeType.GENE,
        content="Require a password policy.",
        source_refs=("dna.product_blueprint",),
        markers=("auth",),
    )

    registry.add(gene)

    assert registry.get("gene.auth.password_policy") == gene
    assert registry.find_by_type(MoleculeType.GENE) == (gene,)


def test_molecule_registry_rejects_duplicate_refs():
    registry = MoleculeRegistry()
    gene = MolecularStructure(
        ref="gene.auth.password_policy",
        molecule_type=MoleculeType.GENE,
        content="Require a password policy.",
    )
    registry.add(gene)

    with pytest.raises(ValueError, match="duplicate molecular structure ref"):
        registry.add(gene)
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_molecules_immune.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.molecules'`.

- [x] **Step 3: Implement molecule registry**

Create `bioscaffold/molecules.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MoleculeType(str, Enum):
    DNA = "dna"
    GENE = "gene"
    PROMOTER = "promoter"
    RNA_TRANSCRIPT = "rna_transcript"
    SPLICED_TRANSCRIPT = "spliced_transcript"
    PLASMID = "plasmid"
    PROTEIN = "protein"
    ANTIGEN = "antigen"
    ANTIBODY = "antibody"


@dataclass(frozen=True)
class MolecularStructure:
    ref: str
    molecule_type: MoleculeType
    content: str
    source_refs: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class MoleculeRegistry:
    def __init__(self) -> None:
        self._structures: dict[str, MolecularStructure] = {}

    def add(self, structure: MolecularStructure) -> MolecularStructure:
        if structure.ref in self._structures:
            raise ValueError(f"duplicate molecular structure ref: {structure.ref}")
        self._structures[structure.ref] = structure
        return structure

    def get(self, ref: str) -> MolecularStructure:
        return self._structures[ref]

    def find_by_type(self, molecule_type: MoleculeType) -> tuple[MolecularStructure, ...]:
        return tuple(
            structure
            for structure in self._structures.values()
            if structure.molecule_type is molecule_type
        )

    def all(self) -> tuple[MolecularStructure, ...]:
        return tuple(self._structures.values())
```

- [x] **Step 4: Run molecule tests**

Run: `python -m pytest tests/test_molecules_immune.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_molecules_immune.py bioscaffold/molecules.py
git commit -m "Add molecule registry"
```

## Task 5: Simulated Bacteria And White Blood Cells

**Files:**
- Modify: `tests/test_molecules_immune.py`
- Create: `bioscaffold/immune.py`

- [x] **Step 1: Add failing immune tests**

Append to `tests/test_molecules_immune.py`:

```python
from bioscaffold.immune import ImmuneSystem, PathogenFixture
from bioscaffold.microtasks import TaskState


def test_pathogen_fixture_injects_inert_plasmid():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )

    task = fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    plasmid = registry.get("plasmid.injected.fake_done.v1")
    assert plasmid.molecule_type is MoleculeType.PLASMID
    assert plasmid.markers == ("fake_completion_marker", "pathogen_fixture")
    assert task.state is TaskState.COMPLETE
    assert task.outputs == ("plasmid.injected.fake_done.v1",)


def test_white_blood_cell_quarantines_known_marker():
    registry = MoleculeRegistry()
    fixture = PathogenFixture(
        fixture_id="bacteria_fake_done",
        defect_marker="fake_completion_marker",
        injected_ref="plasmid.injected.fake_done.v1",
        payload="fake done marker",
    )
    fixture.inject(
        registry,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    task, event = ImmuneSystem(known_markers={"fake_completion_marker"}).inspect(
        registry,
        target_ref="plasmid.injected.fake_done.v1",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.QUARANTINED
    assert event.action == "quarantine"
    assert event.antibody_ref == "antibody.fake_completion_marker"
    assert registry.get("antibody.fake_completion_marker").molecule_type is MoleculeType.ANTIBODY
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_molecules_immune.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.immune'`.

- [x] **Step 3: Implement immune fixtures**

Create `bioscaffold/immune.py`:

```python
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
            outputs=(antibody_ref,),
            metadata={"immune_event_id": event.event_id},
        )
        return task, event
```

- [x] **Step 4: Run immune tests**

Run: `python -m pytest tests/test_molecules_immune.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_molecules_immune.py bioscaffold/immune.py
git commit -m "Add simulated immune hardening fixtures"
```

## Task 6: Generation Review

**Files:**
- Create: `tests/test_generations.py`
- Create: `bioscaffold/generations.py`

- [x] **Step 1: Write failing generation tests**

Create `tests/test_generations.py`:

```python
import pytest

from bioscaffold.generations import Generation, GenerationEngine, GenerationStatus
from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnEngine


def terminal_task(task_id: str, state: TaskState, output: str) -> MicroTask:
    return MicroTask(
        task_id=task_id,
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.VALIDATE,
        target_ref=output,
        agent_hat=AgentHat.VALIDATOR,
    ).with_terminal(state, reason=f"{state.value} evidence", outputs=(output,))


def test_generation_review_requires_closed_turns():
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(Turn(turn_id="turn_000001", generation_id="gen_000001", organism_id="organism_000001"),),
    )

    with pytest.raises(ValueError, match="generation review requires closed turns"):
        GenerationEngine().review(generation, MoleculeRegistry())


def test_generation_review_promotes_only_closed_turn_outputs():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
        )
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(terminal_task("task_000001", TaskState.COMPLETE, "gene.auth.password_policy"),),
        )
    )
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(turn,),
    )

    reviewed = GenerationEngine().review(generation, registry)

    assert reviewed.status is GenerationStatus.REVIEWED
    assert reviewed.promoted_structures == ("gene.auth.password_policy",)
    assert reviewed.quarantined_structures == ()


def test_generation_review_preserves_quarantine_and_immune_memory():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="antibody.fake_completion_marker",
            molecule_type=MoleculeType.ANTIBODY,
            content="signature for fake completion marker",
            markers=("fake_completion_marker",),
        )
    )
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(
                terminal_task(
                    "task_000001",
                    TaskState.QUARANTINED,
                    "plasmid.injected.fake_done.v1",
                ),
            ),
        )
    )
    generation = Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        turns=(turn,),
    )

    reviewed = GenerationEngine().review(generation, registry)

    assert reviewed.promoted_structures == ()
    assert reviewed.quarantined_structures == ("plasmid.injected.fake_done.v1",)
    assert reviewed.immune_memory == ("antibody.fake_completion_marker",)
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_generations.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.generations'`.

- [x] **Step 3: Implement generation review**

Create `bioscaffold/generations.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.microtasks import TaskState
from bioscaffold.molecules import MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnStatus


class GenerationStatus(str, Enum):
    OPEN = "open"
    REVIEWED = "reviewed"


@dataclass(frozen=True)
class Generation:
    generation_id: str
    organism_id: str
    turns: tuple[Turn, ...] = ()
    status: GenerationStatus = GenerationStatus.OPEN
    promoted_structures: tuple[str, ...] = ()
    quarantined_structures: tuple[str, ...] = ()
    immune_memory: tuple[str, ...] = ()


class GenerationEngine:
    def review(self, generation: Generation, registry: MoleculeRegistry) -> Generation:
        open_turns = [turn.turn_id for turn in generation.turns if turn.status is not TurnStatus.CLOSED]
        if open_turns:
            raise ValueError(
                f"generation review requires closed turns: {', '.join(open_turns)}"
            )

        promoted = []
        quarantined = []
        for turn in generation.turns:
            for task in turn.tasks:
                if task.state is TaskState.COMPLETE:
                    promoted.extend(task.outputs)
                if task.state is TaskState.QUARANTINED:
                    quarantined.extend(task.outputs or (task.target_ref,))

        immune_memory = tuple(
            structure.ref
            for structure in registry.find_by_type(MoleculeType.ANTIBODY)
        )
        return replace(
            generation,
            status=GenerationStatus.REVIEWED,
            promoted_structures=tuple(dict.fromkeys(promoted)),
            quarantined_structures=tuple(dict.fromkeys(quarantined)),
            immune_memory=immune_memory,
        )
```

- [x] **Step 4: Run generation tests**

Run: `python -m pytest tests/test_generations.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_generations.py bioscaffold/generations.py
git commit -m "Add generation review engine"
```

## Task 7: Public Exports And Full Verification

**Files:**
- Modify: `tests/test_component_cards.py`
- Modify: `bioscaffold/__init__.py`

- [x] **Step 1: Write failing public export expectation**

Change `test_package_imports` in `tests/test_component_cards.py` to:

```python
def test_package_imports():
    import bioscaffold

    assert bioscaffold.__all__ == [
        "AgentHat",
        "BioCell",
        "BioScale",
        "CellRole",
        "Generation",
        "GenerationEngine",
        "LifecyclePhase",
        "MicroOperation",
        "MicroTask",
        "MolecularStructure",
        "MoleculeRegistry",
        "MoleculeType",
        "TaskState",
        "Turn",
        "TurnEngine",
    ]
```

- [x] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_component_cards.py::test_package_imports -v`

Expected: FAIL because new exports are not present.

- [x] **Step 3: Update public exports**

Replace `bioscaffold/__init__.py` with:

```python
from __future__ import annotations

from bioscaffold.cell import BioCell
from bioscaffold.generations import Generation, GenerationEngine
from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnEngine
from bioscaffold.types import CellRole, LifecyclePhase

__all__ = [
    "AgentHat",
    "BioCell",
    "BioScale",
    "CellRole",
    "Generation",
    "GenerationEngine",
    "LifecyclePhase",
    "MicroOperation",
    "MicroTask",
    "MolecularStructure",
    "MoleculeRegistry",
    "MoleculeType",
    "TaskState",
    "Turn",
    "TurnEngine",
]
```

- [x] **Step 4: Run full verification**

Run: `python -m pytest -v`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit code 0.

- [x] **Step 5: Commit**

```powershell
git add bioscaffold/__init__.py tests/test_component_cards.py
git commit -m "Export turn generation primitives"
```

## Self-Review

Spec coverage:

- Microscopic work source of macroscopic growth: Task 2 and Task 3 define micro-tasks and turn barriers.
- Strict terminal turn states: Task 2 and Task 3 implement terminal states and closure enforcement.
- Generations as review checkpoints: Task 6 implements reviewed generations over closed turns.
- DNA/RNA-level structures: Task 1 and Task 4 add cards and registry support.
- Simulated bacteria and white blood cells: Task 5 implements inert pathogen fixtures and immune inspection.
- One active product organism standard: `organism_id` is present on tasks, turns, and generations in Tasks 2, 3, and 6.
- Simple hat-scoped tasks: Task 2 implements the agent hat policy.

Placeholder scan:

- No plan step uses undefined placeholder content.
- Every code task includes a test, expected failure, implementation, verification command, and commit command.

Type consistency:

- `MicroTask`, `TaskState`, `Turn`, `Generation`, `MoleculeRegistry`, and `MoleculeType` names are consistent across tests and implementation snippets.
