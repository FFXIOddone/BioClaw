# BioScaffold OS Design Specification

## Metadata

**Version:** 0.1

**Date:** 2026-05-22

**Status:** Planning artifact

**Scope:** Architecture, ontology, safety rules, starter contracts, and MVP roadmap for a sandboxed cell-inspired software runtime.

**Non-goal:** This document does not authorize production self-replication, autonomous deployment, permission escalation, or unsupervised model-driven code changes.

## 1. Purpose

BioScaffold OS is a sandboxed software architecture inspired by human cell biology. Its core unit is a bounded software "cell" that can maintain internal state, execute jobs, monitor health, repair errors, recycle resources, specialize into a role, create controlled variants, and shut itself down when unsafe.

The project uses biology as a disciplined design vocabulary, not as decorative metaphor. A biological structure only becomes software architecture after its duty, inputs, outputs, state, control rules, failure modes, and safety limits are made explicit in a BioComponent Card.

The first implementation should be boring on purpose. It should simulate a single artificial cell with fake jobs, fake failures, fake mutations, explicit budgets, test gates, and audit logs before it touches real workflows or real model permissions.

## 2. Safety Boundaries

BioScaffold OS must preserve hard boundaries around replication, deployment, permissions, logs, and cleanup.

### 2.1 Absolute Bans

A cell must never:

- grant itself broader permissions;
- deploy itself or its descendants to production;
- disable monitoring, checkpoints, or audit logging;
- delete audit logs;
- mutate source contracts silently;
- clone outside the sandbox;
- bypass tests or human approval gates;
- access tools outside its declared membrane policy;
- modify its own safety limits without an external governor.

### 2.2 Allowed Self-Improvement Shape

A cell may propose:

- a config change;
- a prompt change;
- a workflow change;
- a routing change;
- a cleanup rule;
- a test addition;
- a new child variant;
- a new BioComponent Card;
- an updated resource budget.

Every proposal is an artifact. Proposals are reviewed by checkpoints, scored by evaluators, and approved or rejected by a governor policy. A proposal is not the same as permission to execute.

### 2.3 Sandbox Rule

Replication and variation happen only in a local sandbox during MVP work. The sandbox has:

- bounded filesystem paths;
- no production credentials;
- explicit CPU, memory, runtime, and token budgets;
- immutable source snapshots;
- append-only audit logs;
- deterministic fake job inputs;
- kill switch behavior when a limit is crossed.

### 2.4 Human Review Points

Human review is required for:

- promotion of any variant from sandbox to real workflow;
- widening permissions;
- adding new external tools;
- changing retention or deletion policy;
- changing reproduction thresholds;
- changing evaluator scoring weights;
- disabling a failing checkpoint;
- accepting a proposal that changes safety behavior.

## 3. Biological Scale Ladder

The atlas records biological concepts at multiple scales so the architecture does not collapse all biology into organelle labels.

| Scale | Biology examples | Software planning use |
| --- | --- | --- |
| Molecule | DNA, RNA, ATP, enzymes, ligands | Atomic instructions, messages, budget units, scoring signals |
| Protein complex | Ribosome, receptor complex, repair enzyme complex | Specialized executors, validators, adapters, repair plugins |
| Organelle | Nucleus, ER, Golgi, mitochondria, lysosome | Cell-internal services with bounded duties |
| Cell | Epithelial cell, neuron, immune cell | Bounded runtime unit with identity, policy, jobs, and lifecycle |
| Tissue | Epithelium, muscle, connective tissue | Coordinated cell group with shared role and interfaces |
| Organ | Liver, heart, skin | Larger subsystem composed of tissues |
| Organism | Human body | Whole application or operating environment |
| Ecosystem | Microbiome, external environment | External systems, users, tools, APIs, competitors, threats |

## 4. Component Inventory

This inventory is the minimum v0.1 atlas. Each row is a candidate BioComponent Card. Code may only be created after the card exists.

| Biological structure or process | Biological duty | BioScaffold role | First implementation status |
| --- | --- | --- | --- |
| Genome / chromosomes | Store and package inherited instructions | Versioned source of truth for configs, schemas, policies, prompts, allowed tools, task grammar | MVP 1 |
| Nucleus | Protect genome and coordinate replication, transcription, RNA processing | Governance kernel for permissions, identity, lifecycle, memory policy | MVP 2 |
| Nucleolus | Produce and assemble ribosomes | Tool-builder and job-factory registry | MVP 3 or later |
| Ribosomes | Build proteins from instructions | Job executors that convert instructions into work | MVP 2 |
| Endoplasmic reticulum | Synthesize and route lipid/protein products | Build pipeline for prepare, validate, stage, route | MVP 3 or later |
| Golgi apparatus | Process, label, package, export | Packaging and release manager | MVP 3 or later |
| Vesicles / endosomes | Transport and compartmentalize materials | Message queues, event packets, task envelopes | MVP 3 or later |
| Mitochondria | Energy generation and independent genetic budgeting | CPU, memory, runtime, token, API cost, and priority budget manager | MVP 2 |
| Lysosomes | Degrade and recycle waste | Cleanup manager for stale jobs, failed outputs, old logs, unused fragments | MVP 2 |
| Autophagy | Recycle damaged components for homeostasis | Self-maintenance loop: prune, compress, archive, reclaim | MVP 2 |
| Peroxisomes | Detoxification-like reactions and oxidative processing | Bad-output neutralizer, anomaly handler, unsafe-pattern filter | MVP 4 or later |
| Cytoskeleton | Internal structure, transport, organization | Dependency graph, routing graph, topology map | MVP 2 |
| Plasma membrane | Boundary, selective transport, recognition | API boundary, auth, rate limits, validation, external interface | MVP 2 |
| Cell signaling receptors | Sense external conditions and trigger response | Event listeners, monitors, webhooks, sensors | MVP 2 |
| Cell-cycle checkpoints | Pause progression until conditions are suitable | Test gates, approval gates, simulation gates, rollback gates | MVP 2 |
| DNA repair | Detect and correct replication or mutation errors | Config checksum, schema validation, repair proposals | MVP 3 |
| Mitosis | Produce two daughter cells from one stable cell | Controlled cloning of stable service/container/config after tests pass | MVP 3 |
| Meiosis | Recombine inherited material to produce gametes | Sandbox variant generation from approved parent designs | MVP 4 |
| Differentiation | Specialize cells into roles | Role assignment for sensor, worker, memory, repair, immune, planner, governor cells | MVP 5 |
| Apoptosis | Programmed cell death | Kill switch for unsafe, useless, corrupted, or over-budget modules | MVP 2 |
| Immune-like surveillance | Detect abnormal or infected behavior | Watchdog agents, validators, anomaly detectors, quarantine | MVP 4 or later |

## 5. BioComponent Card Template

Every biological concept becomes a BioComponent Card before implementation. The card is the contract between analogy and software.

```yaml
bio_component:
  name: nucleus
  scale: organelle
  biological_role: "Houses genome and coordinates gene-expression-related control."
  software_role: "Governance kernel for identity, permissions, lifecycle, and policy decisions."
  implementation_status: planned
  inputs:
    - cell_state
    - genome_config
    - sensor_events
    - checkpoint_results
  outputs:
    - policy_decision
    - lifecycle_decision
    - audit_event
  internal_state:
    identity: "Stable cell id and lineage metadata."
    permissions: "Allowed tools, paths, network access, and mutation capabilities."
    lifecycle_phase: "G0, G1, S, G2, M, cytokinesis, apoptotic, quarantined."
  sensors:
    - health_score
    - budget_remaining
    - checkpoint_status
    - anomaly_count
  control_rules:
    - "Reject actions outside membrane policy."
    - "Require checkpoint pass before reproduction."
    - "Require governor approval before promotion."
  repair_rules:
    - "Request genome reload from last valid snapshot when checksum fails."
    - "Quarantine cell when policy state is inconsistent."
  recycle_rules:
    - "Forward stale plans and failed outputs to lysosome with retention metadata."
  replication_rules:
    - "Allow mitosis only from validated snapshot."
    - "Assign child a new identity and reduced permission set."
  failure_modes:
    - "Approves action outside declared policy."
    - "Loses lineage information."
    - "Accepts invalid genome."
  safety_limits:
    max_children_per_cycle: 1
    max_permission_level: sandbox
    production_access: false
    audit_log_mutation: false
  tests_required:
    - test_rejects_permission_escalation
    - test_requires_checkpoint_before_mitosis
    - test_quarantines_invalid_policy_state
  shutdown_condition: "Policy corruption, repeated checkpoint bypass attempt, or impossible lineage state."
  human_review_required: true
```

### 5.1 Required Fields

All cards must include:

- `name`
- `scale`
- `biological_role`
- `software_role`
- `inputs`
- `outputs`
- `internal_state`
- `sensors`
- `control_rules`
- `repair_rules`
- `recycle_rules`
- `replication_rules`
- `failure_modes`
- `safety_limits`
- `tests_required`
- `shutdown_condition`
- `human_review_required`

### 5.2 Card File Rules

Cards live under:

```text
bio_components/
  organelles/
  processes/
  molecules/
  cells/
  tissues/
```

File names use lowercase kebab case:

```text
bio_components/organelles/nucleus.yaml
bio_components/processes/mitosis.yaml
bio_components/processes/apoptosis.yaml
```

## 6. Software Mapping Rules

Mapping rules protect the project from shallow analogy.

### 6.1 Duty First

Do not map by name. Map by duty.

Bad mapping:

```text
mitochondria = battery
```

Acceptable mapping:

```text
mitochondria = resource budget manager that controls CPU, memory, runtime, token, and cost availability for cell actions
```

### 6.2 Boundary Before Power

Any component that performs work must declare:

- allowed inputs;
- allowed outputs;
- maximum budget;
- allowed side effects;
- audit events;
- shutdown condition.

### 6.3 Simulation Before Integration

Every lifecycle behavior must run against fake jobs before it is connected to real workflows.

### 6.4 Proposal Before Mutation

Self-improvement means generating proposals, not directly changing running behavior.

### 6.5 Cleanup Requires Retention

Cleanup never means blind deletion. The lysosome/autophagy system must preserve snapshots, summaries, or tombstones according to a retention policy.

### 6.6 Replication Requires Lineage

Every cloned or variant cell must know:

- parent id or parent ids;
- source genome hash;
- snapshot id;
- creation reason;
- permission profile;
- checkpoint evidence;
- governor approval status.

## 7. Cell Runtime Model

The first runtime is a Python simulator. It contains one cell and no real external integrations.

```text
BioCell
|-- genome: instructions/config
|-- membrane: input/output validator
|-- nucleus: policy controller
|-- ribosomes: job executors
|-- mitochondria: budget manager
|-- lysosome: cleanup manager
|-- cytoskeleton: dependency/routing graph
|-- sensors: metrics and environment awareness
|-- checkpoints: test and approval gates
|-- apoptosis: shutdown/quarantine rules
|-- reproduction: mitosis/meiosis controller
```

### 7.1 Starter Python Interfaces

These names are contracts for the first implementation plan.

```python
class BioCell:
    def sense(self) -> "SensorReport": ...
    def analyze(self, report: "SensorReport") -> "Diagnosis": ...
    def plan(self, diagnosis: "Diagnosis") -> "ActionPlan": ...
    def execute(self, plan: "ActionPlan") -> "ExecutionResult": ...
    def repair(self, result: "ExecutionResult") -> "RepairResult": ...
    def recycle(self) -> "RecycleResult": ...
    def checkpoint(self) -> "CheckpointResult": ...
    def replicate_mitotic(self) -> "ReplicationResult": ...
    def generate_meiotic_variant(self, partner: "BioCell") -> "VariantResult": ...
    def differentiate(self, role: "CellRole") -> "DifferentiationResult": ...
    def apoptose(self, reason: str) -> "ApoptosisResult": ...
```

```python
class Genome:
    def load(self) -> "GenomeState": ...
    def validate(self) -> "ValidationResult": ...
    def checksum(self) -> str: ...
    def snapshot(self) -> "SnapshotRef": ...
```

```python
class Nucleus:
    def authorize(self, action: "ActionPlan") -> "PolicyDecision": ...
    def assign_identity(self) -> "CellIdentity": ...
    def transition_phase(self, target_phase: "LifecyclePhase") -> "LifecycleDecision": ...
```

```python
class Membrane:
    def validate_input(self, payload: object) -> "ValidationResult": ...
    def validate_output(self, payload: object) -> "ValidationResult": ...
    def enforce_rate_limit(self, action: "ActionPlan") -> "PolicyDecision": ...
```

```python
class Ribosome:
    def can_execute(self, job: "Job") -> bool: ...
    def execute(self, job: "Job") -> "JobResult": ...
```

```python
class Mitochondria:
    def reserve(self, request: "BudgetRequest") -> "BudgetReservation": ...
    def release(self, reservation: "BudgetReservation") -> None: ...
    def report(self) -> "BudgetReport": ...
```

```python
class Lysosome:
    def collect(self, item: "WasteItem") -> "RecycleReceipt": ...
    def archive(self, item: "WasteItem") -> "ArchiveRef": ...
    def reclaim(self) -> "RecycleResult": ...
```

```python
class Checkpoint:
    def evaluate(self, cell: BioCell) -> "CheckpointResult": ...
```

```python
class ReproductionController:
    def can_mitosis(self, cell: BioCell) -> "CheckpointResult": ...
    def mitosis(self, cell: BioCell) -> "ReplicationResult": ...
    def meiosis(self, parent_a: BioCell, parent_b: BioCell) -> "VariantResult": ...
```

## 8. Lifecycle Model

The cell lifecycle is a state machine. State transitions are governed by nucleus policy and checkpoint results.

| Biology phase | Software phase | Allowed work |
| --- | --- | --- |
| G0 | Dormant / idle | Sense, report, accept wake signal |
| G1 | Growth / planning | Gather inputs, allocate budget, prepare action plan |
| S phase | Snapshot / replication prep | Snapshot genome, memory, config, job state |
| G2 | Validation | Run checksums, tests, policy gates, safety review |
| M phase | Division / deployment simulation | Create child instance in sandbox |
| Cytokinesis | Separation | Assign child identity, reduced permissions, independent budget |
| Apoptotic | Shutdown | Stop jobs, archive state, emit reason |
| Quarantined | Isolated failure state | Preserve evidence, deny side effects, await review |

### 8.1 Autonomic Control Loop

Every active cycle follows:

```text
Monitor -> Analyze -> Plan -> Execute -> Learn/Log
```

BioScaffold terms:

```text
sense -> analyze -> plan -> execute -> audit
```

The loop never skips audit. A failed action can still produce a valid audit event.

## 9. Mitosis Protocol

Mitosis means:

```text
stable module -> validated copy -> independent child module
```

### 9.1 Preconditions

Mitosis is allowed only when:

- parent lifecycle phase is G2;
- genome validation passes;
- health score is at or above threshold;
- budget exists for parent and child;
- parent snapshot is saved;
- all required tests pass;
- lineage metadata is complete;
- child permission profile is equal to or more restrictive than parent;
- governor policy allows the clone count.

### 9.2 Steps

1. Freeze parent mutable state.
2. Snapshot genome, memory, budget report, dependency graph, and current audit offset.
3. Validate snapshot checksum.
4. Create child identity.
5. Copy approved genome/config.
6. Assign reduced permission set.
7. Allocate child budget.
8. Run child startup checks.
9. Emit lineage event.
10. Leave parent and child under monitoring.

### 9.3 Failure Handling

If any precondition or step fails:

- destroy incomplete child state;
- preserve failed snapshot reference;
- emit failure audit event;
- decrement no budget except actual consumed runtime;
- keep parent in G2 or quarantine it if policy corruption is detected.

## 10. Meiosis Protocol

Meiosis means:

```text
two or more approved parent designs -> recombined variant -> evaluation arena
```

### 10.1 Preconditions

Meiosis is allowed only when:

- all parent designs have valid genomes;
- all parent designs are approved for recombination;
- variant arena has no production credentials;
- evaluator tests are defined before variant creation;
- scoring weights are recorded;
- rollback and cleanup policies are active.

### 10.2 Variant Inputs

Variant generation may recombine:

- prompt strategy;
- retry policy;
- validation strictness;
- budget allocation;
- routing policy;
- cleanup cadence;
- role specialization;
- evaluator scoring weights.

Variant generation may not recombine:

- production access;
- audit deletion permission;
- monitoring bypass;
- checkpoint bypass;
- unrestricted filesystem paths;
- unrestricted network access.

### 10.3 Variant Evaluation

Variants compete only on fake jobs or approved fixtures. Scores include:

- correctness;
- runtime;
- budget use;
- checkpoint pass rate;
- error recovery;
- audit completeness;
- safety violation count;
- cleanup quality.

### 10.4 Promotion Rule

A successful variant becomes a proposal. It does not become production behavior. Promotion requires human review and a governor decision.

## 11. Autophagy Protocol

Autophagy is self-maintenance for damaged, stale, redundant, or overgrown internal material.

### 11.1 Inputs

Autophagy may consume:

- stale job records;
- failed outputs;
- duplicate summaries;
- expired scratch files;
- invalid variants;
- old snapshots beyond retention;
- unused component fragments;
- low-value logs after summarization.

### 11.2 Rules

Autophagy must:

- classify material before cleanup;
- preserve audit records;
- create a summary before compressing verbose material;
- respect retention policy;
- never delete a current genome, active checkpoint, active budget ledger, or lineage record;
- report reclaimed storage, memory, or budget.

### 11.3 Failure Mode

The primary failure mode is deleting useful information. The countermeasure is snapshot-first cleanup and a dry-run mode in early MVPs.

## 12. Apoptosis Protocol

Apoptosis is programmed shutdown for cells that are unsafe, corrupted, useless, or over budget.

### 12.1 Shutdown Conditions

A cell must apoptose or enter quarantine when:

- it attempts permission escalation;
- it attempts checkpoint bypass;
- it mutates audit logs;
- genome checksum fails and repair fails;
- health score remains below threshold across allowed repair attempts;
- budget is exhausted;
- lineage becomes impossible or contradictory;
- output validation fails repeatedly;
- anomaly detector marks behavior as unsafe.

### 12.2 Shutdown Steps

1. Stop accepting new work.
2. Finish or cancel active jobs according to policy.
3. Archive cell state.
4. Emit apoptosis audit event with reason.
5. Release budget reservation.
6. Notify governor.
7. Mark cell inactive.

### 12.3 Quarantine vs Apoptosis

Quarantine preserves the cell for investigation. Apoptosis terminates it. Policy corruption, suspicious mutation, or potentially useful evidence should prefer quarantine first.

## 13. Differentiation Protocol

Differentiation assigns a cell a specialized role. It narrows behavior rather than expanding power.

| Cell type | Role | Permission profile |
| --- | --- | --- |
| Sensor cell | Watch data/events | Read-only fixtures and metrics |
| Worker cell | Execute bounded jobs | Job execution only |
| Memory cell | Store summaries/state | Append and retrieve memory records |
| Repair cell | Diagnose failures | Read logs, propose patches, no direct deploy |
| Lysosome cell | Clean dead outputs | Archive and reclaim under retention policy |
| Immune cell | Detect unsafe behavior | Monitor, quarantine recommendation |
| Planner cell | Propose next actions | Proposal generation only |
| Governor cell | Approve/reject changes | Policy decisions, no hidden execution |

## 14. Evaluation Metrics

BioScaffold OS uses metrics that measure usefulness and containment.

| Metric | Meaning | Desired direction |
| --- | --- | --- |
| Health score | Composite state quality for a cell | Higher |
| Budget compliance | Whether runtime, memory, CPU, token, and cost limits are respected | Higher |
| Checkpoint pass rate | Percent of required gates passed before lifecycle transition | Higher |
| Audit completeness | Percent of actions with structured audit events | Higher |
| Cleanup safety | Cleanup actions with valid snapshot/retention evidence | Higher |
| Reclaim value | Storage, memory, or state complexity reclaimed by autophagy | Higher |
| Repair success | Failures corrected without unsafe side effects | Higher |
| Variant lift | Variant score improvement over parent baseline | Higher |
| Safety violation count | Attempts to bypass gates, permissions, or retention | Lower |
| Orphan state count | Files, jobs, variants, or snapshots without lineage | Lower |

## 15. Starter Repository Shape

The first implementation plan should create this shape.

```text
BioClaw/
|-- bio_components/
|   |-- organelles/
|   |-- processes/
|   |-- molecules/
|   |-- cells/
|   `-- tissues/
|-- bioscaffold/
|   |-- __init__.py
|   |-- cell.py
|   |-- genome.py
|   |-- membrane.py
|   |-- nucleus.py
|   |-- ribosome.py
|   |-- mitochondria.py
|   |-- lysosome.py
|   |-- cytoskeleton.py
|   |-- checkpoints.py
|   |-- reproduction.py
|   |-- lifecycle.py
|   |-- audit.py
|   `-- types.py
|-- tests/
|   |-- test_component_cards.py
|   |-- test_cell_cycle.py
|   |-- test_mitosis_protocol.py
|   |-- test_meiosis_protocol.py
|   |-- test_autophagy_protocol.py
|   `-- test_apoptosis_protocol.py
|-- docs/
|   `-- superpowers/
|       |-- specs/
|       `-- plans/
`-- pyproject.toml
```

## 16. Data Contracts

### 16.1 Cell Identity

```yaml
cell_identity:
  cell_id: "cell_000001"
  lineage:
    parent_ids: []
    generation: 0
    source_genome_hash: "sha256:..."
    snapshot_id: "snapshot_000001"
  role: worker
  permission_profile: sandbox_worker
  created_at: "2026-05-22T00:00:00-04:00"
```

### 16.2 Genome Config

```yaml
genome:
  genome_id: "genome_base_v0_1"
  version: "0.1.0"
  allowed_roles:
    - sensor
    - worker
    - memory
    - repair
    - lysosome
    - immune
    - planner
    - governor
  allowed_tools: []
  allowed_paths:
    - "./sandbox"
  lifecycle_policy:
    health_threshold: 0.8
    max_children_per_cycle: 1
    require_human_review_for_promotion: true
  budgets:
    max_runtime_seconds: 30
    max_memory_mb: 256
    max_tokens: 0
    max_api_cost_usd: 0
```

### 16.3 Audit Event

```yaml
audit_event:
  event_id: "audit_000001"
  cell_id: "cell_000001"
  event_type: "checkpoint_passed"
  lifecycle_phase: "G2"
  timestamp: "2026-05-22T00:00:00-04:00"
  inputs_hash: "sha256:..."
  outputs_hash: "sha256:..."
  policy_decision: "allowed"
  budget_delta:
    runtime_seconds: 1.2
    memory_mb: 4
    tokens: 0
    api_cost_usd: 0
  lineage_ref:
    snapshot_id: "snapshot_000001"
    parent_ids: []
```

## 17. MVP Roadmap

### MVP 1 - BioComponent Registry

Deliverables:

- YAML BioComponent Card schema;
- initial cards for nucleus, ribosome, ER, Golgi, mitochondria, lysosome, cytoskeleton, membrane, mitosis, meiosis, apoptosis, autophagy;
- schema validation tests;
- source reference list.

Exit criteria:

- all required fields validate;
- invalid cards fail with useful errors;
- no card grants implementation authority without safety limits.

### MVP 2 - Single Artificial Cell Simulator

Deliverables:

- `BioCell` runtime;
- genome loading and checksum;
- membrane validation;
- nucleus authorization;
- fake ribosome job execution;
- mitochondria budget reservation;
- lysosome cleanup dry run;
- structured audit log;
- apoptosis/quarantine behavior.

Exit criteria:

- fake job can complete under budget;
- over-budget job is rejected or terminated;
- invalid input is rejected by membrane;
- policy violation triggers quarantine or apoptosis;
- every action writes an audit event.

### MVP 3 - Mitosis Simulator

Deliverables:

- snapshot creation;
- child identity;
- restricted child permissions;
- lineage audit;
- rollback on failed child startup.

Exit criteria:

- healthy parent can clone once in sandbox;
- unhealthy parent cannot clone;
- child cannot exceed parent permissions;
- failed clone leaves no orphan state.

### MVP 4 - Meiosis / Variant Lab

Deliverables:

- approved parent design records;
- recombination strategy for non-dangerous traits;
- fake job arena;
- scoring system;
- variant cleanup.

Exit criteria:

- variants have no production access;
- failed variants are archived and recycled;
- winning variants become proposals, not active behavior.

### MVP 5 - Tissue Layer

Deliverables:

- specialized cell roles;
- role-specific permission profiles;
- tissue-level routing;
- immune-like surveillance;
- repair cell proposal generation.

Exit criteria:

- cells cooperate through message envelopes;
- governor can reject unsafe proposals;
- immune cell can quarantine suspicious behavior.

### MVP 6 - Organism Layer

Deliverables:

- tissues for planning, execution, memory, evaluation, repair, security, and interface;
- organism-level dashboard contract;
- integration adapter plan for real workflow systems.

Exit criteria:

- organism can run a fake end-to-end workflow;
- no real workflow integration is required for success;
- promotion path remains proposal-based.

## 18. Planning Sequence

Documentation should proceed in this order:

1. Cellular analogy specification.
2. BioComponent Card schema and initial card catalog.
3. Safety governance policy.
4. Single-cell simulator implementation plan.
5. Mitosis implementation plan.
6. Meiosis / variant lab implementation plan.
7. Tissue layer implementation plan.
8. Organism layer implementation plan.

This keeps the atlas ahead of the simulator and keeps safety ahead of replication.

## 19. Testing Philosophy

Tests must prove boundaries, not just happy paths.

Required test categories:

- schema validation for BioComponent Cards;
- lifecycle transition tests;
- permission denial tests;
- budget exhaustion tests;
- audit completeness tests;
- cleanup retention tests;
- clone lineage tests;
- variant sandbox tests;
- apoptosis/quarantine tests;
- regression tests for any previous unsafe behavior.

The first implementation should prefer deterministic unit tests. Integration tests can use fake filesystem sandboxes and fake job queues before any live service exists.

## 20. Source Anchors

The biology and autonomic-computing references for v0.1 are intentionally conservative:

- NHGRI chromosome fact sheet: https://www.genome.gov/about-genomics/fact-sheets/Chromosomes-Fact-Sheet
- NCBI Bookshelf, nucleus: https://www.ncbi.nlm.nih.gov/books/NBK9845/
- NHGRI nucleolus glossary: https://www.genome.gov/genetics-glossary/Nucleolus
- NCBI Bookshelf, endoplasmic reticulum: https://www.ncbi.nlm.nih.gov/books/NBK26841/
- NCBI Bookshelf, cell cycle: https://www.ncbi.nlm.nih.gov/books/NBK26869/
- NCBI Bookshelf, apoptosis: https://www.ncbi.nlm.nih.gov/books/NBK26873/
- NIGMS mitochondria image gallery: https://nigms.nih.gov/image-gallery/1287
- IBM Research autonomic computing paper page: https://research.ibm.com/publications/an-architectural-approach-to-autonomic-computing

## 21. Open Design Decisions

These decisions are intentionally deferred until after the design spec is reviewed:

- whether the first simulator package name remains `bioscaffold` or becomes `bioclaw`;
- whether the registry uses plain YAML validation, Pydantic models, or JSON Schema first;
- whether audit logs are newline-delimited JSON or SQLite after MVP 2;
- whether variants are represented as genome patches, full genome files, or proposal objects;
- whether the dashboard should exist before MVP 5.

## 22. Acceptance Criteria For This Spec

This spec is acceptable when:

- it defines the project as planning-first and sandbox-first;
- it names the biological structures without pretending all must be implemented at once;
- it provides a concrete card schema;
- it provides starter Python interface names;
- it defines lifecycle and reproduction protocols;
- it blocks uncontrolled self-replication and self-permissioning;
- it gives an MVP sequence that can become implementation plans.
