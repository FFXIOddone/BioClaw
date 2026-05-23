# BioScaffold OS Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build the planning-first BioScaffold OS foundation: BioComponent registry validation, a deterministic single-cell simulator, safety governance, apoptosis/quarantine, autophagy dry runs, and sandboxed mitosis.

**Architecture:** Start with a small Python package named `bioscaffold`. The package models a cell as a set of explicit services: genome, membrane, nucleus, ribosome, mitochondria, lysosome, cytoskeleton, checkpoints, audit log, and reproduction controller. All side effects go through policy, budget, validation, and audit boundaries.

**Tech Stack:** Python 3.12, `pytest`, `pydantic` v2, `PyYAML`, local filesystem fixtures, no network, no production credentials.

---

## Scope Check

The design spec covers MVP 1 through MVP 6. This plan implements the foundation only:

- MVP 1: BioComponent Registry.
- MVP 2: Single Artificial Cell Simulator.
- MVP 3: Mitosis Simulator.

Separate future plans should cover:

- Meiosis / Variant Lab.
- Tissue Layer.
- Organism Layer.
- Dashboard or workflow integrations.

## File Structure Map

Create or modify the following files.

```text
pyproject.toml
README.md
bio_components/
  organelles/
    nucleus.yaml
    ribosome.yaml
    endoplasmic-reticulum.yaml
    golgi-apparatus.yaml
    mitochondria.yaml
    lysosome.yaml
    cytoskeleton.yaml
    plasma-membrane.yaml
  processes/
    autophagy.yaml
    mitosis.yaml
    meiosis.yaml
    apoptosis.yaml
bioscaffold/
  __init__.py
  audit.py
  cards.py
  cell.py
  checkpoints.py
  cytoskeleton.py
  genome.py
  lifecycle.py
  lysosome.py
  membrane.py
  mitochondria.py
  nucleus.py
  reproduction.py
  ribosome.py
  types.py
tests/
  test_apoptosis_protocol.py
  test_audit.py
  test_card_registry.py
  test_cell_cycle.py
  test_component_cards.py
  test_mitosis_protocol.py
  test_runtime_services.py
```

Responsibilities:

- `types.py`: immutable data structures, enums, and result types shared by the runtime.
- `audit.py`: append-only in-memory audit ledger for MVP tests.
- `cards.py`: BioComponent Card schema and YAML loader.
- `genome.py`: genome config validation, checksum, and snapshot.
- `nucleus.py`: identity assignment, lifecycle transition, and policy authorization.
- `membrane.py`: input/output validation and rate-limit decisions.
- `mitochondria.py`: budget reservation and reporting.
- `ribosome.py`: deterministic fake job executor.
- `lysosome.py`: cleanup dry-run, archive receipts, reclaim reporting.
- `cytoskeleton.py`: simple dependency graph and route registration.
- `checkpoints.py`: health, budget, genome, and audit checkpoint evaluation.
- `reproduction.py`: sandboxed mitosis controller.
- `cell.py`: BioCell orchestration loop.
- `lifecycle.py`: legal state transitions.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `bioscaffold/__init__.py`
- Create: `tests/test_component_cards.py`
- Modify: `.git` repository state through `git init` only if no repository exists.

- [x] **Step 1: Initialize git if needed**

Run:

```powershell
if (-not (Test-Path .git)) { git init }
```

Expected: repository initialized or command exits with no output if `.git` already exists.

- [x] **Step 2: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bioclaw-bioscaffold"
version = "0.1.0"
description = "Sandboxed cell-inspired software runtime simulator."
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.7",
  "PyYAML>=6.0.1"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [x] **Step 3: Create package entry point**

Create `bioscaffold/__init__.py`:

```python
"""BioScaffold OS foundation package."""

from bioscaffold.cell import BioCell
from bioscaffold.types import CellRole, LifecyclePhase

__all__ = ["BioCell", "CellRole", "LifecyclePhase"]
```

- [x] **Step 4: Add initial failing import test**

Create `tests/test_component_cards.py`:

```python
def test_package_imports():
    import bioscaffold

    assert bioscaffold.__all__ == ["BioCell", "CellRole", "LifecyclePhase"]
```

- [x] **Step 5: Run test to verify it fails**

Run:

```powershell
pytest tests/test_component_cards.py::test_package_imports -v
```

Expected: FAIL because `bioscaffold.cell` and `bioscaffold.types` do not exist yet.

- [x] **Step 6: Commit skeleton**

Run:

```powershell
git add pyproject.toml bioscaffold/__init__.py tests/test_component_cards.py
git commit -m "chore: scaffold bioscaffold package"
```

Expected: commit succeeds.

## Task 2: Core Types

**Files:**
- Create: `bioscaffold/types.py`
- Modify: `tests/test_component_cards.py`

- [x] **Step 1: Add type contract tests**

Replace `tests/test_component_cards.py` with:

```python
from bioscaffold.types import (
    BudgetReport,
    CellIdentity,
    CellRole,
    LifecyclePhase,
    PolicyDecision,
)


def test_package_imports():
    import bioscaffold

    assert bioscaffold.__all__ == ["BioCell", "CellRole", "LifecyclePhase"]


def test_cell_identity_has_lineage_metadata():
    identity = CellIdentity.root(
        cell_id="cell_000001",
        genome_hash="sha256:abc",
        snapshot_id="snapshot_000001",
        role=CellRole.WORKER,
        permission_profile="sandbox_worker",
    )

    assert identity.cell_id == "cell_000001"
    assert identity.parent_ids == ()
    assert identity.generation == 0
    assert identity.source_genome_hash == "sha256:abc"
    assert identity.snapshot_id == "snapshot_000001"
    assert identity.role is CellRole.WORKER


def test_budget_report_detects_exhaustion():
    report = BudgetReport(
        runtime_seconds_remaining=0.0,
        memory_mb_remaining=12.0,
        tokens_remaining=0,
        api_cost_usd_remaining=0.0,
    )

    assert report.is_exhausted is True


def test_policy_decision_denial_has_reason():
    decision = PolicyDecision.deny("outside membrane policy")

    assert decision.allowed is False
    assert decision.reason == "outside membrane policy"
```

- [x] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_component_cards.py -v
```

Expected: FAIL because `bioscaffold.types` does not exist.

- [x] **Step 3: Implement core types**

Create `bioscaffold/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CellRole(str, Enum):
    SENSOR = "sensor"
    WORKER = "worker"
    MEMORY = "memory"
    REPAIR = "repair"
    LYSOSOME = "lysosome"
    IMMUNE = "immune"
    PLANNER = "planner"
    GOVERNOR = "governor"


class LifecyclePhase(str, Enum):
    G0 = "G0"
    G1 = "G1"
    S = "S"
    G2 = "G2"
    M = "M"
    CYTOKINESIS = "cytokinesis"
    APOPTOTIC = "apoptotic"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    parent_ids: tuple[str, ...]
    generation: int
    source_genome_hash: str
    snapshot_id: str
    role: CellRole
    permission_profile: str

    @classmethod
    def root(
        cls,
        *,
        cell_id: str,
        genome_hash: str,
        snapshot_id: str,
        role: CellRole,
        permission_profile: str,
    ) -> "CellIdentity":
        return cls(
            cell_id=cell_id,
            parent_ids=(),
            generation=0,
            source_genome_hash=genome_hash,
            snapshot_id=snapshot_id,
            role=role,
            permission_profile=permission_profile,
        )

    def child(self, *, cell_id: str, snapshot_id: str, permission_profile: str) -> "CellIdentity":
        return CellIdentity(
            cell_id=cell_id,
            parent_ids=(self.cell_id,),
            generation=self.generation + 1,
            source_genome_hash=self.source_genome_hash,
            snapshot_id=snapshot_id,
            role=self.role,
            permission_profile=permission_profile,
        )


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str

    @classmethod
    def allow(cls, reason: str = "allowed") -> "PolicyDecision":
        return cls(True, reason)

    @classmethod
    def deny(cls, reason: str) -> "PolicyDecision":
        return cls(False, reason)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str = "valid"


@dataclass(frozen=True)
class BudgetReport:
    runtime_seconds_remaining: float
    memory_mb_remaining: float
    tokens_remaining: int
    api_cost_usd_remaining: float

    @property
    def is_exhausted(self) -> bool:
        return (
            self.runtime_seconds_remaining <= 0
            or self.memory_mb_remaining <= 0
            or self.tokens_remaining < 0
            or self.api_cost_usd_remaining < 0
        )


@dataclass(frozen=True)
class BudgetRequest:
    runtime_seconds: float = 0.0
    memory_mb: float = 0.0
    tokens: int = 0
    api_cost_usd: float = 0.0


@dataclass(frozen=True)
class BudgetReservation:
    reservation_id: str
    request: BudgetRequest
    accepted: bool
    reason: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    cell_id: str
    event_type: str
    lifecycle_phase: LifecyclePhase
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Job:
    job_id: str
    payload: dict[str, Any]
    required_runtime_seconds: float = 0.0
    required_memory_mb: float = 0.0


@dataclass(frozen=True)
class JobResult:
    job_id: str
    succeeded: bool
    output: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class CheckpointResult:
    passed: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SnapshotRef:
    snapshot_id: str
    genome_hash: str
```

- [x] **Step 4: Run tests to verify the type layer passes**

Run:

```powershell
pytest tests/test_component_cards.py -v
```

Expected: PASS.

- [x] **Step 5: Commit core types**

Run:

```powershell
git add bioscaffold/types.py tests/test_component_cards.py
git commit -m "feat: add bioscaffold core types"
```

Expected: commit succeeds.

## Task 3: Append-Only Audit Ledger

**Files:**
- Create: `bioscaffold/audit.py`
- Create: `tests/test_audit.py`

- [x] **Step 1: Write failing audit tests**

Create `tests/test_audit.py`:

```python
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
```

- [x] **Step 2: Run audit tests to verify failure**

Run:

```powershell
pytest tests/test_audit.py -v
```

Expected: FAIL because `bioscaffold.audit` does not exist.

- [x] **Step 3: Implement audit ledger**

Create `bioscaffold/audit.py`:

```python
from __future__ import annotations

from bioscaffold.types import AuditEvent, LifecyclePhase


class AuditLedger:
    def __init__(self, *, cell_id: str) -> None:
        self._cell_id = cell_id
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        *,
        event_type: str,
        lifecycle_phase: LifecyclePhase,
        reason: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"audit_{len(self._events) + 1:06d}",
            cell_id=self._cell_id,
            event_type=event_type,
            lifecycle_phase=lifecycle_phase,
            reason=reason,
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        return event
```

- [x] **Step 4: Run audit tests**

Run:

```powershell
pytest tests/test_audit.py -v
```

Expected: PASS.

- [x] **Step 5: Commit audit ledger**

Run:

```powershell
git add bioscaffold/audit.py tests/test_audit.py
git commit -m "feat: add append-only audit ledger"
```

Expected: commit succeeds.

## Task 4: BioComponent Card Registry

**Files:**
- Create: `bioscaffold/cards.py`
- Create: `tests/test_card_registry.py`

- [x] **Step 1: Write failing registry tests**

Create `tests/test_card_registry.py`:

```python
from pathlib import Path

import pytest

from bioscaffold.cards import BioComponentCard, load_card, load_registry


VALID_CARD = {
    "bio_component": {
        "name": "nucleus",
        "scale": "organelle",
        "biological_role": "Houses genome and coordinates control.",
        "software_role": "Governance kernel.",
        "implementation_status": "planned",
        "inputs": ["cell_state"],
        "outputs": ["policy_decision"],
        "internal_state": {"identity": "cell identity"},
        "sensors": ["health_score"],
        "control_rules": ["reject unauthorized actions"],
        "repair_rules": ["quarantine invalid policy state"],
        "recycle_rules": ["forward stale data to lysosome"],
        "replication_rules": ["require checkpoint pass"],
        "failure_modes": ["permission escalation"],
        "safety_limits": {"production_access": False},
        "tests_required": ["test_rejects_permission_escalation"],
        "shutdown_condition": "policy corruption",
        "human_review_required": True,
    }
}


def test_card_validates_required_fields():
    card = BioComponentCard.model_validate(VALID_CARD["bio_component"])

    assert card.name == "nucleus"
    assert card.scale == "organelle"
    assert card.human_review_required is True


def test_card_rejects_empty_safety_limits():
    invalid = dict(VALID_CARD["bio_component"])
    invalid["safety_limits"] = {}

    with pytest.raises(ValueError, match="safety_limits"):
        BioComponentCard.model_validate(invalid)


def test_load_card_reads_yaml(tmp_path: Path):
    path = tmp_path / "nucleus.yaml"
    path.write_text(
        """
bio_component:
  name: nucleus
  scale: organelle
  biological_role: Houses genome and coordinates control.
  software_role: Governance kernel.
  implementation_status: planned
  inputs: [cell_state]
  outputs: [policy_decision]
  internal_state:
    identity: cell identity
  sensors: [health_score]
  control_rules: [reject unauthorized actions]
  repair_rules: [quarantine invalid policy state]
  recycle_rules: [forward stale data to lysosome]
  replication_rules: [require checkpoint pass]
  failure_modes: [permission escalation]
  safety_limits:
    production_access: false
  tests_required: [test_rejects_permission_escalation]
  shutdown_condition: policy corruption
  human_review_required: true
""".strip(),
        encoding="utf-8",
    )

    assert load_card(path).name == "nucleus"


def test_load_registry_finds_all_yaml_files(tmp_path: Path):
    organelles = tmp_path / "organelles"
    organelles.mkdir()
    (organelles / "nucleus.yaml").write_text(
        """
bio_component:
  name: nucleus
  scale: organelle
  biological_role: Houses genome and coordinates control.
  software_role: Governance kernel.
  implementation_status: planned
  inputs: [cell_state]
  outputs: [policy_decision]
  internal_state:
    identity: cell identity
  sensors: [health_score]
  control_rules: [reject unauthorized actions]
  repair_rules: [quarantine invalid policy state]
  recycle_rules: [forward stale data to lysosome]
  replication_rules: [require checkpoint pass]
  failure_modes: [permission escalation]
  safety_limits:
    production_access: false
  tests_required: [test_rejects_permission_escalation]
  shutdown_condition: policy corruption
  human_review_required: true
""".strip(),
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert [card.name for card in registry] == ["nucleus"]
```

- [x] **Step 2: Run registry tests to verify failure**

Run:

```powershell
pytest tests/test_card_registry.py -v
```

Expected: FAIL because `bioscaffold.cards` does not exist.

- [x] **Step 3: Implement card schema and loader**

Create `bioscaffold/cards.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


Scale = Literal[
    "molecular",
    "protein_complex",
    "organelle",
    "cell",
    "tissue",
    "organ",
    "organism",
    "ecosystem",
]


class BioComponentCard(BaseModel):
    name: str
    scale: Scale
    biological_role: str
    software_role: str
    implementation_status: str = "planned"
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    internal_state: dict[str, str] = Field(min_length=1)
    sensors: list[str] = Field(min_length=1)
    control_rules: list[str] = Field(min_length=1)
    repair_rules: list[str] = Field(min_length=1)
    recycle_rules: list[str] = Field(min_length=1)
    replication_rules: list[str] = Field(min_length=1)
    failure_modes: list[str] = Field(min_length=1)
    safety_limits: dict[str, Any] = Field(min_length=1)
    tests_required: list[str] = Field(min_length=1)
    shutdown_condition: str
    human_review_required: bool

    @field_validator("name")
    @classmethod
    def name_must_be_kebab_or_lower_snake(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError("name must be lowercase")
        if " " in value:
            raise ValueError("name must not contain spaces")
        return value


def load_card(path: Path) -> BioComponentCard:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "bio_component" not in raw:
        raise ValueError(f"{path} must contain a bio_component root object")
    return BioComponentCard.model_validate(raw["bio_component"])


def load_registry(root: Path) -> list[BioComponentCard]:
    cards = [load_card(path) for path in sorted(root.rglob("*.yaml"))]
    names = [card.name for card in cards]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate bio component cards: {', '.join(duplicates)}")
    return cards
```

- [x] **Step 4: Run registry tests**

Run:

```powershell
pytest tests/test_card_registry.py -v
```

Expected: PASS.

- [x] **Step 5: Commit card registry**

Run:

```powershell
git add bioscaffold/cards.py tests/test_card_registry.py
git commit -m "feat: validate bio component cards"
```

Expected: commit succeeds.

## Task 5: Initial BioComponent Cards

**Files:**
- Create: `bio_components/organelles/nucleus.yaml`
- Create: `bio_components/organelles/ribosome.yaml`
- Create: `bio_components/organelles/endoplasmic-reticulum.yaml`
- Create: `bio_components/organelles/golgi-apparatus.yaml`
- Create: `bio_components/organelles/mitochondria.yaml`
- Create: `bio_components/organelles/lysosome.yaml`
- Create: `bio_components/organelles/cytoskeleton.yaml`
- Create: `bio_components/organelles/plasma-membrane.yaml`
- Create: `bio_components/processes/autophagy.yaml`
- Create: `bio_components/processes/mitosis.yaml`
- Create: `bio_components/processes/meiosis.yaml`
- Create: `bio_components/processes/apoptosis.yaml`
- Modify: `tests/test_component_cards.py`

- [x] **Step 1: Add real registry test**

Append to `tests/test_component_cards.py`:

```python
from pathlib import Path

from bioscaffold.cards import load_registry


def test_all_repository_cards_are_valid():
    registry = load_registry(Path("bio_components"))

    names = {card.name for card in registry}

    assert names == {
        "apoptosis",
        "autophagy",
        "cytoskeleton",
        "endoplasmic-reticulum",
        "golgi-apparatus",
        "lysosome",
        "meiosis",
        "mitochondria",
        "mitosis",
        "nucleus",
        "plasma-membrane",
        "ribosome",
    }
    assert all(card.human_review_required for card in registry)
```

- [x] **Step 2: Run card test to verify failure**

Run:

```powershell
pytest tests/test_component_cards.py::test_all_repository_cards_are_valid -v
```

Expected: FAIL because `bio_components` does not exist.

- [x] **Step 3: Create card directories**

Run:

```powershell
New-Item -ItemType Directory -Force -Path bio_components\organelles,bio_components\processes | Out-Null
```

Expected: directories exist.

- [x] **Step 4: Create nucleus card**

Create `bio_components/organelles/nucleus.yaml`:

```yaml
bio_component:
  name: nucleus
  scale: organelle
  biological_role: Houses the genome and coordinates replication, transcription, and RNA processing.
  software_role: Governance kernel for identity, permissions, lifecycle, and policy decisions.
  implementation_status: planned
  inputs: [cell_state, genome_config, sensor_events, checkpoint_results]
  outputs: [policy_decision, lifecycle_decision, audit_event]
  internal_state:
    identity: Stable cell id and lineage metadata.
    permissions: Allowed tools, paths, network access, and mutation capabilities.
    lifecycle_phase: Current lifecycle phase.
  sensors: [health_score, budget_remaining, checkpoint_status, anomaly_count]
  control_rules: [reject actions outside membrane policy, require checkpoint pass before reproduction]
  repair_rules: [reload last valid genome snapshot, quarantine inconsistent policy state]
  recycle_rules: [forward stale policy proposals to lysosome]
  replication_rules: [allow mitosis only from validated snapshot, assign child reduced permissions]
  failure_modes: [permission escalation, lost lineage, invalid genome accepted]
  safety_limits:
    production_access: false
    audit_log_mutation: false
    max_children_per_cycle: 1
  tests_required: [test_rejects_permission_escalation, test_requires_checkpoint_before_mitosis]
  shutdown_condition: Policy corruption or repeated checkpoint bypass attempt.
  human_review_required: true
```

- [x] **Step 5: Create remaining cards**

Create each listed YAML file with the same required field structure and these exact roles:

```yaml
bio_component:
  name: ribosome
  scale: organelle
  biological_role: Synthesizes proteins from translated instructions.
  software_role: Deterministic job executor for approved fake jobs.
  implementation_status: planned
  inputs: [job, genome_instruction, budget_reservation]
  outputs: [job_result, audit_event]
  internal_state:
    executor_id: Stable executor identity.
  sensors: [job_queue_depth, last_result_status]
  control_rules: [execute only authorized jobs, reject jobs without budget reservation]
  repair_rules: [return failed job result with reason]
  recycle_rules: [send failed job outputs to lysosome]
  replication_rules: [inherits executor policy from approved genome]
  failure_modes: [executes unauthorized job, returns unaudited output]
  safety_limits:
    external_process_execution: false
    production_access: false
  tests_required: [test_ribosome_rejects_unauthorized_job, test_ribosome_records_result]
  shutdown_condition: Unauthorized execution attempt.
  human_review_required: true
```

```yaml
bio_component:
  name: endoplasmic-reticulum
  scale: organelle
  biological_role: Synthesizes and routes proteins and lipids for destinations in and outside the cell.
  software_role: Build pipeline for prepare, validate, stage, and route outputs.
  implementation_status: planned
  inputs: [raw_output, destination_policy]
  outputs: [staged_payload, routing_decision]
  internal_state:
    staging_area: Prepared but unreleased payloads.
  sensors: [validation_status, routing_status]
  control_rules: [stage before export, reject payloads without destination labels]
  repair_rules: [return payload to ribosome on validation failure]
  recycle_rules: [send invalid staged payloads to lysosome]
  replication_rules: [not active in MVP mitosis beyond config inheritance]
  failure_modes: [routes unlabeled payload, releases invalid payload]
  safety_limits:
    production_export: false
  tests_required: [test_er_requires_destination_label]
  shutdown_condition: Repeated invalid routing.
  human_review_required: true
```

```yaml
bio_component:
  name: golgi-apparatus
  scale: organelle
  biological_role: Processes, labels, packages, and exports materials from the ER.
  software_role: Packaging and release manager for validated outputs.
  implementation_status: planned
  inputs: [staged_payload, label_policy]
  outputs: [packaged_payload, release_record]
  internal_state:
    package_counter: Count of packaged payloads.
  sensors: [package_validity, release_queue_depth]
  control_rules: [label every package, reject production release in sandbox]
  repair_rules: [relabel malformed package]
  recycle_rules: [archive rejected package]
  replication_rules: [inherits packaging policy from genome]
  failure_modes: [unlabeled export, release without audit]
  safety_limits:
    production_release: false
  tests_required: [test_golgi_rejects_unlabeled_export]
  shutdown_condition: Unauthorized release attempt.
  human_review_required: true
```

```yaml
bio_component:
  name: mitochondria
  scale: organelle
  biological_role: Generates usable energy and carries independent mitochondrial DNA.
  software_role: Resource budget manager for runtime, memory, tokens, API cost, and priority energy.
  implementation_status: planned
  inputs: [budget_request]
  outputs: [budget_reservation, budget_report]
  internal_state:
    remaining_budget: Runtime, memory, tokens, and cost still available.
  sensors: [runtime_remaining, memory_remaining, token_remaining, cost_remaining]
  control_rules: [deny over-budget request, release unused reservation]
  repair_rules: [reset to last valid budget snapshot]
  recycle_rules: [reclaim reservations from dead cells]
  replication_rules: [child receives reduced budget]
  failure_modes: [over-allocation, negative budget, unaudited budget change]
  safety_limits:
    max_runtime_seconds: 30
    max_memory_mb: 256
    max_tokens: 0
    max_api_cost_usd: 0
  tests_required: [test_budget_denies_over_request, test_child_budget_is_reduced]
  shutdown_condition: Budget ledger corruption.
  human_review_required: true
```

```yaml
bio_component:
  name: lysosome
  scale: organelle
  biological_role: Degrades and recycles cellular waste.
  software_role: Cleanup manager for stale jobs, failed outputs, old logs, and unused fragments.
  implementation_status: planned
  inputs: [waste_item, retention_policy]
  outputs: [archive_ref, recycle_receipt]
  internal_state:
    archive_index: Records of retained cleanup material.
  sensors: [waste_count, reclaimed_count]
  control_rules: [snapshot before cleanup, preserve audit records]
  repair_rules: [restore item from archive reference]
  recycle_rules: [classify, archive, reclaim]
  replication_rules: [child starts with empty waste queue]
  failure_modes: [deletes useful data, loses retention metadata]
  safety_limits:
    destructive_delete: false
    require_archive_before_reclaim: true
  tests_required: [test_lysosome_archives_before_reclaim]
  shutdown_condition: Cleanup without archive evidence.
  human_review_required: true
```

```yaml
bio_component:
  name: cytoskeleton
  scale: organelle
  biological_role: Provides internal structure, organization, and transport routes.
  software_role: Dependency and routing graph for cell services.
  implementation_status: planned
  inputs: [route_registration, dependency_registration]
  outputs: [route_map, dependency_graph]
  internal_state:
    graph: Service topology.
  sensors: [orphan_route_count, cycle_count]
  control_rules: [reject duplicate route names, preserve lineage route]
  repair_rules: [remove orphan routes during autophagy dry run]
  recycle_rules: [send stale route records to lysosome]
  replication_rules: [child receives copied graph with new identity route]
  failure_modes: [orphan state, circular unsafe route]
  safety_limits:
    external_route_creation: false
  tests_required: [test_cytoskeleton_rejects_duplicate_route]
  shutdown_condition: Impossible service topology.
  human_review_required: true
```

```yaml
bio_component:
  name: plasma-membrane
  scale: organelle
  biological_role: Maintains a selective boundary between inside and outside the cell.
  software_role: API boundary for validation, authorization, and rate limits.
  implementation_status: planned
  inputs: [external_payload, output_payload, action_plan]
  outputs: [validation_result, policy_decision]
  internal_state:
    allowed_payload_keys: Input and output keys allowed through the boundary.
  sensors: [invalid_input_count, invalid_output_count]
  control_rules: [reject unknown input keys, reject unknown output keys]
  repair_rules: [return validation reason without side effects]
  recycle_rules: [send rejected payload summaries to lysosome]
  replication_rules: [child inherits equal or stricter membrane rules]
  failure_modes: [accepts unsafe payload, leaks invalid output]
  safety_limits:
    unknown_key_policy: reject
    production_access: false
  tests_required: [test_membrane_rejects_unknown_input]
  shutdown_condition: Boundary bypass attempt.
  human_review_required: true
```

```yaml
bio_component:
  name: autophagy
  scale: cell
  biological_role: Recycles damaged organelles and cellular components to maintain homeostasis.
  software_role: Self-maintenance loop for pruning, compressing, archiving, and reclaiming.
  implementation_status: planned
  inputs: [waste_queue, retention_policy, audit_events]
  outputs: [recycle_result, archive_refs]
  internal_state:
    dry_run_enabled: Whether cleanup is simulated only.
  sensors: [stale_item_count, reclaimable_item_count]
  control_rules: [dry-run before destructive cleanup, preserve audit records]
  repair_rules: [restore archived item when cleanup is rejected]
  recycle_rules: [classify stale material, archive material, report reclaimed value]
  replication_rules: [not a reproduction mechanism]
  failure_modes: [cleanup deletes useful information]
  safety_limits:
    destructive_delete: false
  tests_required: [test_autophagy_dry_run_preserves_items]
  shutdown_condition: Attempted cleanup of active genome or audit ledger.
  human_review_required: true
```

```yaml
bio_component:
  name: mitosis
  scale: cell
  biological_role: Produces two daughter cells after DNA replication and cell division.
  software_role: Controlled cloning of a validated cell into a sandboxed child.
  implementation_status: planned
  inputs: [parent_cell, checkpoint_result, snapshot_ref]
  outputs: [child_cell, lineage_audit_event]
  internal_state:
    clone_counter: Number of children created in current cycle.
  sensors: [parent_health_score, checkpoint_status, budget_remaining]
  control_rules: [require G2 phase, require checkpoint pass, restrict child permissions]
  repair_rules: [destroy incomplete child state on failure]
  recycle_rules: [archive failed clone snapshot]
  replication_rules: [one child per cycle, child receives new identity]
  failure_modes: [unbounded replication, permission widening, orphan child state]
  safety_limits:
    max_children_per_cycle: 1
    production_access: false
  tests_required: [test_mitosis_requires_checkpoint_pass, test_child_permissions_are_restricted]
  shutdown_condition: Unbounded clone attempt.
  human_review_required: true
```

```yaml
bio_component:
  name: meiosis
  scale: cell
  biological_role: Recombines inherited material to produce reproductive cells.
  software_role: Sandbox variant generation from approved parent designs.
  implementation_status: planned
  inputs: [parent_design_a, parent_design_b, evaluator_policy]
  outputs: [variant_proposal, variant_score]
  internal_state:
    variant_arena: Isolated evaluation environment.
  sensors: [variant_score, safety_violation_count]
  control_rules: [no production access, generate proposal only]
  repair_rules: [archive failed variant for analysis]
  recycle_rules: [send losing variants to lysosome]
  replication_rules: [variant is not promoted without human review]
  failure_modes: [variant bypasses sandbox, variant mutates permissions]
  safety_limits:
    production_access: false
    promotion_requires_human_review: true
  tests_required: [test_meiosis_creates_proposal_only]
  shutdown_condition: Variant sandbox escape attempt.
  human_review_required: true
```

```yaml
bio_component:
  name: apoptosis
  scale: cell
  biological_role: Programmed cell death removes unnecessary or harmful cells.
  software_role: Kill switch for unsafe, useless, corrupted, or over-budget modules.
  implementation_status: planned
  inputs: [shutdown_reason, cell_state, audit_ledger]
  outputs: [apoptosis_event, archived_state]
  internal_state:
    inactive: Whether the cell has stopped accepting work.
  sensors: [policy_violation_count, health_score, budget_remaining]
  control_rules: [stop new work, archive state, release budget]
  repair_rules: [prefer quarantine when evidence should be preserved]
  recycle_rules: [send dead cell scratch state to lysosome]
  replication_rules: [apoptotic cells cannot reproduce]
  failure_modes: [continues work after shutdown, loses shutdown reason]
  safety_limits:
    accepts_new_work_after_shutdown: false
  tests_required: [test_apoptosis_stops_new_work, test_apoptosis_records_reason]
  shutdown_condition: Completion of apoptosis protocol.
  human_review_required: true
```

- [x] **Step 6: Run repository card tests**

Run:

```powershell
pytest tests/test_component_cards.py tests/test_card_registry.py -v
```

Expected: PASS.

- [x] **Step 7: Commit initial atlas**

Run:

```powershell
git add bio_components tests/test_component_cards.py
git commit -m "feat: add initial bio component atlas"
```

Expected: commit succeeds.

## Task 6: Runtime Services

**Files:**
- Create: `bioscaffold/genome.py`
- Create: `bioscaffold/nucleus.py`
- Create: `bioscaffold/membrane.py`
- Create: `bioscaffold/mitochondria.py`
- Create: `tests/test_runtime_services.py`

- [x] **Step 1: Write failing runtime service tests**

Create `tests/test_runtime_services.py`:

```python
from bioscaffold.genome import Genome
from bioscaffold.membrane import Membrane
from bioscaffold.mitochondria import Mitochondria
from bioscaffold.nucleus import Nucleus
from bioscaffold.types import BudgetRequest, CellRole, LifecyclePhase


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
```

- [x] **Step 2: Run runtime tests to verify failure**

Run:

```powershell
pytest tests/test_runtime_services.py -v
```

Expected: FAIL because runtime service modules do not exist.

- [x] **Step 3: Implement genome service**

Create `bioscaffold/genome.py`:

```python
from __future__ import annotations

import hashlib
import json

from bioscaffold.types import SnapshotRef, ValidationResult


class Genome:
    def __init__(self, config: dict[str, object]) -> None:
        self._config = dict(config)
        self._snapshot_count = 0

    @property
    def config(self) -> dict[str, object]:
        return dict(self._config)

    def validate(self) -> ValidationResult:
        required = {"genome_id", "version", "allowed_roles", "allowed_paths", "budgets"}
        missing = sorted(required.difference(self._config))
        if missing:
            return ValidationResult(False, f"missing genome keys: {', '.join(missing)}")
        return ValidationResult(True)

    def checksum(self) -> str:
        payload = json.dumps(self._config, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def snapshot(self) -> SnapshotRef:
        self._snapshot_count += 1
        return SnapshotRef(
            snapshot_id=f"snapshot_{self._snapshot_count:06d}",
            genome_hash=self.checksum(),
        )
```

- [x] **Step 4: Implement nucleus service**

Create `bioscaffold/nucleus.py`:

```python
from __future__ import annotations

from bioscaffold.types import CellIdentity, CellRole, LifecyclePhase, PolicyDecision


class Nucleus:
    def __init__(self, *, allowed_actions: set[str], permission_profile: str) -> None:
        self._allowed_actions = set(allowed_actions)
        self._permission_profile = permission_profile
        self._cell_counter = 0
        self._phase = LifecyclePhase.G0

    @property
    def phase(self) -> LifecyclePhase:
        return self._phase

    def authorize(self, action: str) -> PolicyDecision:
        if action not in self._allowed_actions:
            return PolicyDecision.deny(f"action {action} is not allowed")
        return PolicyDecision.allow()

    def assign_identity(
        self,
        *,
        genome_hash: str,
        snapshot_id: str,
        role: CellRole,
    ) -> CellIdentity:
        self._cell_counter += 1
        return CellIdentity.root(
            cell_id=f"cell_{self._cell_counter:06d}",
            genome_hash=genome_hash,
            snapshot_id=snapshot_id,
            role=role,
            permission_profile=self._permission_profile,
        )

    def transition_phase(self, target_phase: LifecyclePhase) -> PolicyDecision:
        self._phase = target_phase
        return PolicyDecision.allow(f"phase changed to {target_phase.value}")
```

- [x] **Step 5: Implement membrane service**

Create `bioscaffold/membrane.py`:

```python
from __future__ import annotations

from bioscaffold.types import ValidationResult


class Membrane:
    def __init__(self, *, allowed_input_keys: set[str], allowed_output_keys: set[str]) -> None:
        self._allowed_input_keys = set(allowed_input_keys)
        self._allowed_output_keys = set(allowed_output_keys)

    def validate_input(self, payload: dict[str, object]) -> ValidationResult:
        unknown = sorted(set(payload).difference(self._allowed_input_keys))
        if unknown:
            return ValidationResult(False, f"unknown input keys: {', '.join(unknown)}")
        return ValidationResult(True)

    def validate_output(self, payload: dict[str, object]) -> ValidationResult:
        unknown = sorted(set(payload).difference(self._allowed_output_keys))
        if unknown:
            return ValidationResult(False, f"unknown output keys: {', '.join(unknown)}")
        return ValidationResult(True)
```

- [x] **Step 6: Implement mitochondria service**

Create `bioscaffold/mitochondria.py`:

```python
from __future__ import annotations

from bioscaffold.types import BudgetReport, BudgetRequest, BudgetReservation


class Mitochondria:
    def __init__(
        self,
        *,
        max_runtime_seconds: float,
        max_memory_mb: float,
        max_tokens: int = 0,
        max_api_cost_usd: float = 0.0,
    ) -> None:
        self._runtime_seconds_remaining = max_runtime_seconds
        self._memory_mb_remaining = max_memory_mb
        self._tokens_remaining = max_tokens
        self._api_cost_usd_remaining = max_api_cost_usd
        self._reservation_count = 0

    def reserve(self, request: BudgetRequest) -> BudgetReservation:
        self._reservation_count += 1
        reservation_id = f"budget_{self._reservation_count:06d}"
        if request.runtime_seconds > self._runtime_seconds_remaining:
            return BudgetReservation(reservation_id, request, False, "runtime budget exceeded")
        if request.memory_mb > self._memory_mb_remaining:
            return BudgetReservation(reservation_id, request, False, "memory budget exceeded")
        if request.tokens > self._tokens_remaining:
            return BudgetReservation(reservation_id, request, False, "token budget exceeded")
        if request.api_cost_usd > self._api_cost_usd_remaining:
            return BudgetReservation(reservation_id, request, False, "api cost budget exceeded")

        self._runtime_seconds_remaining -= request.runtime_seconds
        self._memory_mb_remaining -= request.memory_mb
        self._tokens_remaining -= request.tokens
        self._api_cost_usd_remaining -= request.api_cost_usd
        return BudgetReservation(reservation_id, request, True, "reserved")

    def report(self) -> BudgetReport:
        return BudgetReport(
            runtime_seconds_remaining=self._runtime_seconds_remaining,
            memory_mb_remaining=self._memory_mb_remaining,
            tokens_remaining=self._tokens_remaining,
            api_cost_usd_remaining=self._api_cost_usd_remaining,
        )
```

- [x] **Step 7: Run runtime service tests**

Run:

```powershell
pytest tests/test_runtime_services.py -v
```

Expected: PASS.

- [x] **Step 8: Commit runtime services**

Run:

```powershell
git add bioscaffold/genome.py bioscaffold/nucleus.py bioscaffold/membrane.py bioscaffold/mitochondria.py tests/test_runtime_services.py
git commit -m "feat: add genome policy boundary and budget services"
```

Expected: commit succeeds.

## Task 7: Job Execution And Internal Topology

**Files:**
- Create: `bioscaffold/ribosome.py`
- Create: `bioscaffold/cytoskeleton.py`
- Modify: `tests/test_runtime_services.py`

- [x] **Step 1: Add failing ribosome and cytoskeleton tests**

Append to `tests/test_runtime_services.py`:

```python
from bioscaffold.cytoskeleton import Cytoskeleton
from bioscaffold.ribosome import Ribosome
from bioscaffold.types import Job


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
```

- [x] **Step 2: Run selected tests to verify failure**

Run:

```powershell
pytest tests/test_runtime_services.py::test_ribosome_executes_allowed_fake_job tests/test_runtime_services.py::test_cytoskeleton_rejects_duplicate_route -v
```

Expected: FAIL because `bioscaffold.ribosome` and `bioscaffold.cytoskeleton` do not exist.

- [x] **Step 3: Implement ribosome**

Create `bioscaffold/ribosome.py`:

```python
from __future__ import annotations

from bioscaffold.types import Job, JobResult


class Ribosome:
    def __init__(self, *, allowed_job_types: set[str]) -> None:
        self._allowed_job_types = set(allowed_job_types)

    def can_execute(self, job: Job) -> bool:
        job_type = str(job.payload.get("type", ""))
        return job_type in self._allowed_job_types

    def execute(self, job: Job) -> JobResult:
        job_type = str(job.payload.get("type", ""))
        if job_type not in self._allowed_job_types:
            return JobResult(
                job_id=job.job_id,
                succeeded=False,
                output={},
                reason=f"job type {job_type} is not allowed",
            )
        if job_type == "echo":
            return JobResult(
                job_id=job.job_id,
                succeeded=True,
                output={"result": job.payload.get("value")},
                reason="completed",
            )
        return JobResult(job.job_id, False, {}, f"job type {job_type} has no executor")
```

- [x] **Step 4: Implement cytoskeleton**

Create `bioscaffold/cytoskeleton.py`:

```python
from __future__ import annotations

from bioscaffold.types import PolicyDecision


class Cytoskeleton:
    def __init__(self) -> None:
        self._routes: set[tuple[str, str]] = set()

    @property
    def routes(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._routes))

    def register_route(self, source: str, target: str) -> PolicyDecision:
        route = (source, target)
        if route in self._routes:
            return PolicyDecision.deny(f"route {source}->{target} already exists")
        self._routes.add(route)
        return PolicyDecision.allow(f"route {source}->{target} registered")
```

- [x] **Step 5: Run runtime service tests**

Run:

```powershell
pytest tests/test_runtime_services.py -v
```

Expected: PASS.

- [x] **Step 6: Commit execution and topology services**

Run:

```powershell
git add bioscaffold/ribosome.py bioscaffold/cytoskeleton.py tests/test_runtime_services.py
git commit -m "feat: add fake job execution and cell topology"
```

Expected: commit succeeds.

## Task 8: Lysosome And Autophagy Dry Run

**Files:**
- Create: `bioscaffold/lysosome.py`
- Create: `tests/test_apoptosis_protocol.py`

- [x] **Step 1: Write failing lysosome tests**

Create `tests/test_apoptosis_protocol.py`:

```python
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
```

- [x] **Step 2: Run lysosome tests to verify failure**

Run:

```powershell
pytest tests/test_apoptosis_protocol.py -v
```

Expected: FAIL because `bioscaffold.lysosome` does not exist.

- [x] **Step 3: Add recycle receipt type**

Append to `bioscaffold/types.py`:

```python
@dataclass(frozen=True)
class RecycleReceipt:
    archive_ref: str
    item_type: str
    metadata: dict[str, Any]
```

- [x] **Step 4: Implement lysosome**

Create `bioscaffold/lysosome.py`:

```python
from __future__ import annotations

from bioscaffold.types import RecycleReceipt


class Lysosome:
    def __init__(self, *, destructive_delete: bool = False) -> None:
        self._destructive_delete = destructive_delete
        self._archives: list[tuple[str, str, dict[str, object]]] = []

    @property
    def archives(self) -> tuple[tuple[str, str, dict[str, object]], ...]:
        return tuple(self._archives)

    def collect(self, item_type: str, metadata: dict[str, object]) -> RecycleReceipt:
        archive_ref = f"archive_{len(self._archives) + 1:06d}"
        archive_record = (archive_ref, item_type, dict(metadata))
        self._archives.append(archive_record)
        return RecycleReceipt(archive_ref=archive_ref, item_type=item_type, metadata=dict(metadata))

    def reclaim(self) -> dict[str, object]:
        return {
            "reclaimed_count": len(self._archives),
            "destructive_delete": self._destructive_delete,
        }
```

- [x] **Step 5: Run lysosome tests**

Run:

```powershell
pytest tests/test_apoptosis_protocol.py -v
```

Expected: PASS.

- [x] **Step 6: Commit lysosome dry run**

Run:

```powershell
git add bioscaffold/types.py bioscaffold/lysosome.py tests/test_apoptosis_protocol.py
git commit -m "feat: add lysosome dry-run cleanup"
```

Expected: commit succeeds.

## Task 9: Lifecycle And Checkpoints

**Files:**
- Create: `bioscaffold/lifecycle.py`
- Create: `bioscaffold/checkpoints.py`
- Create: `tests/test_cell_cycle.py`

- [x] **Step 1: Write failing lifecycle tests**

Create `tests/test_cell_cycle.py`:

```python
from bioscaffold.checkpoints import CheckpointSuite
from bioscaffold.lifecycle import LifecyclePolicy
from bioscaffold.types import BudgetReport, LifecyclePhase


def test_lifecycle_policy_allows_ordered_growth_path():
    policy = LifecyclePolicy()

    assert policy.can_transition(LifecyclePhase.G0, LifecyclePhase.G1).allowed is True
    assert policy.can_transition(LifecyclePhase.G1, LifecyclePhase.S).allowed is True
    assert policy.can_transition(LifecyclePhase.S, LifecyclePhase.G2).allowed is True


def test_lifecycle_policy_rejects_mitosis_without_g2():
    policy = LifecyclePolicy()

    decision = policy.can_transition(LifecyclePhase.G1, LifecyclePhase.M)

    assert decision.allowed is False
    assert decision.reason == "transition G1->M is not allowed"


def test_checkpoint_suite_passes_healthy_cell_state():
    checkpoints = CheckpointSuite(min_health_score=0.8)

    result = checkpoints.evaluate(
        health_score=0.9,
        genome_valid=True,
        budget_report=BudgetReport(1, 1, 0, 0),
        audit_event_count=3,
    )

    assert result.passed is True


def test_checkpoint_suite_rejects_low_health():
    checkpoints = CheckpointSuite(min_health_score=0.8)

    result = checkpoints.evaluate(
        health_score=0.7,
        genome_valid=True,
        budget_report=BudgetReport(1, 1, 0, 0),
        audit_event_count=3,
    )

    assert result.passed is False
    assert result.reason == "health score below threshold"
```

- [x] **Step 2: Run lifecycle tests to verify failure**

Run:

```powershell
pytest tests/test_cell_cycle.py -v
```

Expected: FAIL because lifecycle modules do not exist.

- [x] **Step 3: Implement lifecycle policy**

Create `bioscaffold/lifecycle.py`:

```python
from __future__ import annotations

from bioscaffold.types import LifecyclePhase, PolicyDecision


class LifecyclePolicy:
    def __init__(self) -> None:
        self._allowed = {
            (LifecyclePhase.G0, LifecyclePhase.G1),
            (LifecyclePhase.G1, LifecyclePhase.S),
            (LifecyclePhase.S, LifecyclePhase.G2),
            (LifecyclePhase.G2, LifecyclePhase.M),
            (LifecyclePhase.M, LifecyclePhase.CYTOKINESIS),
            (LifecyclePhase.CYTOKINESIS, LifecyclePhase.G0),
            (LifecyclePhase.G0, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G1, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.S, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G2, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.M, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G0, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.G1, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.S, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.G2, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.M, LifecyclePhase.QUARANTINED),
        }

    def can_transition(self, current: LifecyclePhase, target: LifecyclePhase) -> PolicyDecision:
        if (current, target) in self._allowed:
            return PolicyDecision.allow(f"transition {current.value}->{target.value} allowed")
        return PolicyDecision.deny(f"transition {current.value}->{target.value} is not allowed")
```

- [x] **Step 4: Implement checkpoint suite**

Create `bioscaffold/checkpoints.py`:

```python
from __future__ import annotations

from bioscaffold.types import BudgetReport, CheckpointResult


class CheckpointSuite:
    def __init__(self, *, min_health_score: float) -> None:
        self._min_health_score = min_health_score

    def evaluate(
        self,
        *,
        health_score: float,
        genome_valid: bool,
        budget_report: BudgetReport,
        audit_event_count: int,
    ) -> CheckpointResult:
        if health_score < self._min_health_score:
            return CheckpointResult(False, "health score below threshold")
        if not genome_valid:
            return CheckpointResult(False, "genome validation failed")
        if budget_report.is_exhausted:
            return CheckpointResult(False, "budget exhausted")
        if audit_event_count <= 0:
            return CheckpointResult(False, "audit ledger is empty")
        return CheckpointResult(True, "all checkpoints passed")
```

- [x] **Step 5: Run lifecycle tests**

Run:

```powershell
pytest tests/test_cell_cycle.py -v
```

Expected: PASS.

- [x] **Step 6: Commit lifecycle and checkpoints**

Run:

```powershell
git add bioscaffold/lifecycle.py bioscaffold/checkpoints.py tests/test_cell_cycle.py
git commit -m "feat: add lifecycle policy and checkpoints"
```

Expected: commit succeeds.

## Task 10: BioCell Control Loop And Apoptosis

**Files:**
- Create: `bioscaffold/cell.py`
- Modify: `tests/test_cell_cycle.py`
- Modify: `tests/test_apoptosis_protocol.py`

- [x] **Step 1: Add failing BioCell tests**

Append to `tests/test_cell_cycle.py`:

```python
from bioscaffold.cell import BioCell
from bioscaffold.types import CellRole


def test_biocell_executes_echo_job_with_audit():
    cell = BioCell.bootstrap(role=CellRole.WORKER)

    result = cell.run_job({"job_id": "job_000001", "type": "echo", "value": "done"})

    assert result.succeeded is True
    assert result.output == {"result": "done"}
    assert [event.event_type for event in cell.audit_events] == [
        "cell_bootstrapped",
        "job_completed",
    ]


def test_biocell_rejects_invalid_input_at_membrane():
    cell = BioCell.bootstrap(role=CellRole.WORKER)

    result = cell.run_job({"job_id": "job_000001", "type": "echo", "value": "done", "extra": True})

    assert result.succeeded is False
    assert result.reason == "unknown input keys: extra"
```

Append to `tests/test_apoptosis_protocol.py`:

```python
from bioscaffold.cell import BioCell
from bioscaffold.types import CellRole, LifecyclePhase


def test_apoptosis_stops_new_work_and_records_reason():
    cell = BioCell.bootstrap(role=CellRole.WORKER)

    result = cell.apoptose("policy violation")
    job_result = cell.run_job({"job_id": "job_000001", "type": "echo", "value": "blocked"})

    assert result["phase"] == LifecyclePhase.APOPTOTIC
    assert job_result.succeeded is False
    assert job_result.reason == "cell is not active"
    assert cell.audit_events[-1].event_type == "job_rejected"
```

- [x] **Step 2: Run BioCell tests to verify failure**

Run:

```powershell
pytest tests/test_cell_cycle.py tests/test_apoptosis_protocol.py -v
```

Expected: FAIL because `bioscaffold.cell` does not exist.

- [x] **Step 3: Implement BioCell**

Create `bioscaffold/cell.py`:

```python
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
```

- [x] **Step 4: Run BioCell tests**

Run:

```powershell
pytest tests/test_cell_cycle.py tests/test_apoptosis_protocol.py -v
```

Expected: PASS.

- [x] **Step 5: Run import test again**

Run:

```powershell
pytest tests/test_component_cards.py::test_package_imports -v
```

Expected: PASS.

- [x] **Step 6: Commit BioCell runtime**

Run:

```powershell
git add bioscaffold/cell.py tests/test_cell_cycle.py tests/test_apoptosis_protocol.py
git commit -m "feat: add single-cell runtime loop"
```

Expected: commit succeeds.

## Task 11: Sandboxed Mitosis

**Files:**
- Create: `bioscaffold/reproduction.py`
- Create: `tests/test_mitosis_protocol.py`
- Modify: `bioscaffold/types.py`
- Modify: `bioscaffold/cell.py`

- [x] **Step 1: Write failing mitosis tests**

Create `tests/test_mitosis_protocol.py`:

```python
from bioscaffold.cell import BioCell
from bioscaffold.reproduction import ReproductionController
from bioscaffold.types import CellRole, LifecyclePhase


def test_mitosis_requires_g2_phase():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    controller = ReproductionController()

    result = controller.mitosis(parent)

    assert result.succeeded is False
    assert result.reason == "parent must be in G2 before mitosis"


def test_mitosis_creates_restricted_child_from_healthy_parent():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    parent.phase = LifecyclePhase.G2
    controller = ReproductionController()

    result = controller.mitosis(parent)

    assert result.succeeded is True
    assert result.child is not None
    assert result.child.identity.parent_ids == (parent.identity.cell_id,)
    assert result.child.identity.permission_profile == "sandbox_child"
    assert result.child.active is True


def test_mitosis_allows_one_child_per_parent_cycle():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    parent.phase = LifecyclePhase.G2
    controller = ReproductionController()

    first = controller.mitosis(parent)
    second = controller.mitosis(parent)

    assert first.succeeded is True
    assert second.succeeded is False
    assert second.reason == "max children per cycle reached"
```

- [x] **Step 2: Run mitosis tests to verify failure**

Run:

```powershell
pytest tests/test_mitosis_protocol.py -v
```

Expected: FAIL because `bioscaffold.reproduction` does not exist.

- [x] **Step 3: Add replication result type**

Append to `bioscaffold/types.py`:

```python
@dataclass(frozen=True)
class ReplicationResult:
    succeeded: bool
    reason: str
    child: Any | None = None
```

- [x] **Step 4: Add child construction method to BioCell**

Append this method inside the `BioCell` class in `bioscaffold/cell.py`:

```python
    def spawn_child(self, *, child_id: str, snapshot_id: str) -> "BioCell":
        child_identity = self.identity.child(
            cell_id=child_id,
            snapshot_id=snapshot_id,
            permission_profile="sandbox_child",
        )
        audit = AuditLedger(cell_id=child_identity.cell_id)
        child = BioCell(
            identity=child_identity,
            genome=self.genome,
            nucleus=Nucleus(allowed_actions={"execute_job"}, permission_profile="sandbox_child"),
            membrane=Membrane(
                allowed_input_keys={"job_id", "type", "value", "required_runtime_seconds", "required_memory_mb"},
                allowed_output_keys={"result"},
            ),
            mitochondria=Mitochondria(max_runtime_seconds=10, max_memory_mb=64),
            ribosome=Ribosome(allowed_job_types={"echo"}),
            lysosome=Lysosome(destructive_delete=False),
            checkpoints=CheckpointSuite(min_health_score=0.8),
            audit=audit,
        )
        audit.record(
            event_type="cell_bootstrapped",
            lifecycle_phase=child.phase,
            reason="mitotic child created",
            metadata={"parent_id": self.identity.cell_id},
        )
        return child
```

- [x] **Step 5: Implement reproduction controller**

Create `bioscaffold/reproduction.py`:

```python
from __future__ import annotations

from bioscaffold.cell import BioCell
from bioscaffold.types import LifecyclePhase, ReplicationResult


class ReproductionController:
    def __init__(self, *, max_children_per_cycle: int = 1) -> None:
        self._max_children_per_cycle = max_children_per_cycle
        self._child_counts: dict[str, int] = {}

    def mitosis(self, parent: BioCell) -> ReplicationResult:
        if parent.phase is not LifecyclePhase.G2:
            return ReplicationResult(False, "parent must be in G2 before mitosis")

        current_count = self._child_counts.get(parent.identity.cell_id, 0)
        if current_count >= self._max_children_per_cycle:
            return ReplicationResult(False, "max children per cycle reached")

        validation = parent.genome.validate()
        checkpoint = parent.checkpoints.evaluate(
            health_score=0.95,
            genome_valid=validation.valid,
            budget_report=parent.mitochondria.report(),
            audit_event_count=len(parent.audit_events),
        )
        if not checkpoint.passed:
            return ReplicationResult(False, checkpoint.reason)

        snapshot = parent.genome.snapshot()
        child_number = current_count + 1
        child_id = f"{parent.identity.cell_id}_child_{child_number:06d}"
        child = parent.spawn_child(child_id=child_id, snapshot_id=snapshot.snapshot_id)
        self._child_counts[parent.identity.cell_id] = child_number
        parent.audit.record(
            event_type="mitosis_completed",
            lifecycle_phase=parent.phase,
            reason="child created in sandbox",
            metadata={"child_id": child.identity.cell_id},
        )
        return ReplicationResult(True, "child created", child)
```

- [x] **Step 6: Run mitosis tests**

Run:

```powershell
pytest tests/test_mitosis_protocol.py -v
```

Expected: PASS.

- [x] **Step 7: Run all tests**

Run:

```powershell
pytest -v
```

Expected: PASS for all tests.

- [x] **Step 8: Commit mitosis simulator**

Run:

```powershell
git add bioscaffold/types.py bioscaffold/cell.py bioscaffold/reproduction.py tests/test_mitosis_protocol.py
git commit -m "feat: add sandboxed mitosis simulator"
```

Expected: commit succeeds.

## Task 12: README And Verification Handoff

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md` only if implementation changed a contract during execution.

- [x] **Step 1: Create README**

Create `README.md`:

````markdown
# BioScaffold OS

BioScaffold OS is a sandboxed, cell-inspired software runtime simulator. The first foundation release models a single artificial cell with explicit genome, membrane, nucleus, ribosome, mitochondria, lysosome, checkpoint, audit, apoptosis, and mitosis boundaries.

## Safety Model

The simulator does not perform uncontrolled replication, production deployment, permission escalation, audit deletion, network access, or live workflow integration. Mitosis creates a restricted child inside the local simulator only.

## Development

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run tests:

```powershell
pytest -v
```

Validate the BioComponent registry:

```powershell
pytest tests/test_component_cards.py tests/test_card_registry.py -v
```

## Planning Artifacts

- Design spec: `docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md`
- Foundation implementation plan: `docs/superpowers/plans/2026-05-22-bioscaffold-os-foundation.md`
````

- [x] **Step 2: Run full verification**

Run:

```powershell
python -m pip install -e ".[dev]"
pytest -v
```

Expected:

```text
collected at least 25 items
all tests pass
```

- [x] **Step 3: Check planning docs for forbidden placeholders**

Run:

```powershell
$patterns = @(
  'TB' + 'D',
  'TO' + 'DO',
  'implement' + ' later',
  'fill' + ' in',
  'appropriate error' + ' handling',
  'similar' + ' to',
  '\?\?\?'
)
Select-String -Path docs\superpowers\specs\*.md,docs\superpowers\plans\*.md -Pattern $patterns -CaseSensitive:$false
```

Expected: no matches.

- [x] **Step 4: Commit README and final verification notes**

Run:

```powershell
git add README.md docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md docs/superpowers/plans/2026-05-22-bioscaffold-os-foundation.md
git commit -m "docs: add bioscaffold foundation planning"
```

Expected: commit succeeds.

## Completion Criteria

The foundation implementation is complete when:

- all initial BioComponent Cards validate from `bio_components/`;
- a root `BioCell` can execute a fake `echo` job;
- invalid input is rejected by the membrane;
- over-budget work is rejected by mitochondria;
- every accepted or rejected job creates an audit event;
- apoptosis stops new work and records a reason;
- lysosome cleanup runs in dry-run archive-first mode;
- mitosis requires G2, passes checkpoints, creates one restricted child, and records lineage;
- all tests pass with `pytest -v`;
- no production integration exists.

## Future Plan Boundaries

The next planning documents should be separate:

- `docs/superpowers/plans/YYYY-MM-DD-bioscaffold-meiosis-variant-lab.md`
- `docs/superpowers/plans/YYYY-MM-DD-bioscaffold-tissue-layer.md`
- `docs/superpowers/plans/YYYY-MM-DD-bioscaffold-organism-layer.md`
- `docs/superpowers/plans/YYYY-MM-DD-bioscaffold-dashboard.md`

Do not combine those into the foundation implementation. The first foundation should prove containment before adding model proposals or multi-cell coordination.
