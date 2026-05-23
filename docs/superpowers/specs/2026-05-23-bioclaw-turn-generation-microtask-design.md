# BioClaw Turn/Generation Micro-Task Design Specification

## Metadata

**Version:** 0.1

**Date:** 2026-05-23

**Status:** Approved design for implementation planning

**Scope:** Turn barriers, generation checkpoints, microscopic task grammar, DNA/RNA product growth, and simulated immune hardening for a single active product organism.

**Extends:** `docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md`

**Non-goal:** This document does not authorize real malware behavior, autonomous deployment, permission widening, uncontrolled self-replication, or broad agent tasks such as "build the product."

## 1. Purpose

BioClaw should emulate product delivery from microscopic biological process upward. The system does not start by assigning agents large ambiguous jobs. It starts with tiny, auditable operations that compose into larger structures over turns and generations.

The end goal remains product delivery:

```text
genes -> molecular operations -> cells/modules -> tissues/subsystems -> organs/capabilities -> organism/product
```

The workflow interpretation is:

- organism = actual product;
- birth = product building begins;
- growth = microscopic completed tasks compose into higher structures;
- immune hardening = simulated defects and defensive responses improve future behavior;
- death = product is completed, delivered, archived, and removed from active build flow.

Death is a successful terminal lifecycle state. Failure states are infection, quarantine, necrosis, blocked growth, or aborted development.

## 2. Core Correction

The first foundation spec modeled a single cell runtime. This spec corrects the next layer: the runtime must be driven by turns, generations, and microscopic tasks.

The key design rule is:

```text
Smaller structure means simpler task.
```

Agents should not receive a task like:

```text
Build authentication.
```

They should receive simple operations like:

```text
Find the matching requirement gene.
Transcribe the gene into a work transcript.
Splice the transcript to remove inactive clauses.
Bind the transcript to an eligible builder.
Produce one artifact fragment.
Validate the fragment.
Quarantine the fragment if it carries a defect marker.
Promote the fragment if it is stable.
```

Complexity comes from composition, not from giving an agent a complex instruction.

## 3. Scale Ladder

BioClaw's scale ladder maps biological scale to product-workflow scale.

| Scale | Biological structure | Product workflow structure | Example operation |
| --- | --- | --- | --- |
| Molecular | Gene, promoter, RNA, plasmid, antigen | Requirement, activation rule, work order, injected defect, defect marker | Find, copy, splice, bind, flag |
| Protein | Protein, enzyme, antibody | Artifact fragment, validator, regression signature | Produce, validate, neutralize |
| Cell | Specialized cell | Bounded module or local work compartment | Assemble, repair, quarantine |
| Tissue | Coordinated cells | Subsystem made of modules | Route, integrate, stabilize |
| Organ | Tissue group with purpose | Product capability | Package, verify, expose |
| Organism | Whole body | Product | Birth, grow, harden, deliver, archive |

The implementation should start at the molecular scale and climb only when lower-level outputs are stable.

## 4. Turn Model

A turn is one synchronized cycle of microscopic work.

Each turn contains a finite batch of micro-tasks. A turn may not advance until every task reaches one of these terminal states:

- `complete`
- `failed`
- `blocked`
- `quarantined`

There is no silent carry-forward. Unfinished work must be converted into a terminal state with evidence. The next turn may create follow-up tasks from that evidence, but the current turn must close cleanly first.

### 4.1 Turn Invariants

A valid turn must record:

- turn id;
- generation id;
- organism id;
- input structures available at turn start;
- assigned micro-tasks;
- agent hat used for each task;
- terminal state for every task;
- outputs created;
- defects injected;
- immune responses;
- audit events;
- promotion, quarantine, or rejection decisions.

### 4.2 Turn Barrier

The turn barrier enforces:

```text
all micro-tasks terminal -> evaluate outputs -> create next-turn proposals -> close turn
```

If one task cannot finish, it must become `blocked`, `failed`, or `quarantined` with a reason. The reason becomes input for the next turn or the generation review.

## 5. Generation Model

A generation is a bounded group of completed turns.

Generations are the product's evolution clock. A generation does not mean uncontrolled mutation. It means the system pauses after a set of closed turns and asks what stable growth occurred.

Generation review evaluates:

- new genes discovered or refined;
- RNA transcripts produced;
- artifact fragments completed;
- modules/cells assembled;
- tests or antibodies created;
- bacteria attacks observed;
- immune responses that worked;
- quarantined material;
- unresolved blockers;
- structures promoted to the next scale.

### 5.1 Generation Outputs

A generation can output:

- accepted genes;
- rejected genes;
- refined promoters;
- active transcript templates;
- stable artifact fragments;
- new immune signatures;
- quarantine records;
- proposed next-generation tasks;
- a higher-scale structure promotion.

### 5.2 Promotion Rule

A structure can promote upward only when the lower-level evidence is complete.

Examples:

- A gene can become an RNA task only after its activation conditions are satisfied.
- A transcript can become an artifact task only after splicing and validation.
- An artifact fragment can become part of a cell/module only after validation and immune inspection.
- A cell/module can become part of a tissue/subsystem only after integration checks.

## 6. Micro-Task Grammar

The micro-task grammar should be intentionally small. Each task should name one operation, one target, one expected output, and one terminal condition.

```yaml
micro_task:
  task_id: task_000001
  turn_id: turn_000001
  generation_id: gen_000001
  organism_id: organism_000001
  scale: molecular
  operation: find
  target_ref: gene.auth.require_password_policy
  agent_hat: gene_scout
  inputs:
    - genome.product_requirements
  expected_output: located_gene_ref
  terminal_states:
    complete: "Gene reference found and checksum recorded."
    failed: "Search completed and no matching gene exists."
    blocked: "Genome source unavailable or invalid."
    quarantined: "Gene contains contradictory or hostile markers."
```

### 6.1 Starter Operations

The first operation set should include:

- `find`
- `copy`
- `splice`
- `bind`
- `transcribe`
- `translate`
- `produce`
- `validate`
- `inject`
- `detect`
- `quarantine`
- `neutralize`
- `record`
- `promote`
- `archive`

Each operation should be small enough that a 3-4 agent OpenClaw run can execute many tasks without requiring broad context in any single task.

## 7. Agent Hat Model

Agents are not permanent specialists. An agent wears a hat for a task, and the hat defines the allowed operation shape.

Initial hats:

| Hat | Duty | Typical operations |
| --- | --- | --- |
| `gene_scout` | Locate matching genes and requirement fragments | find, record |
| `splicer` | Remove inactive or contradictory clauses from transcripts | splice, validate |
| `transcriber` | Convert active genes into RNA work orders | copy, transcribe |
| `ribosome_worker` | Convert transcripts into artifact fragments | bind, translate, produce |
| `validator` | Check fragments against local rules | validate, record |
| `bacteria` | Inject controlled defects for hardening | inject, record |
| `white_blood_cell` | Detect and respond to defect markers | detect, quarantine, neutralize |
| `macrophage` | Archive evidence and clean damaged material | quarantine, archive |
| `memory_cell` | Turn learned defects into future signatures | record, promote |
| `generation_reviewer` | Decide what promotes after closed turns | validate, promote, archive |

Every task must declare its hat. A hat narrows behavior. It does not grant broad authority.

## 8. DNA/RNA Product Growth

The DNA/RNA layer is the target microscopic layer. BioClaw does not need atom-level modeling.

### 8.1 Structures

| Structure | Workflow role |
| --- | --- |
| DNA | Durable product blueprint, constraints, and inherited decisions |
| Gene | One requirement, capability, quality rule, constraint, or delivery rule |
| Promoter | Activation condition for a gene |
| RNA transcript | Active work order derived from a gene |
| Spliced transcript | Work order after inactive or invalid clauses are removed |
| Plasmid | Injected external instruction bundle, usually from bacteria fixtures |
| Protein | Produced artifact fragment, test fragment, doc fragment, or validation result |
| Antigen | Marker that identifies a defect, contradiction, or hostile pattern |
| Antibody | Learned regression signature or response rule |

### 8.2 Growth Flow

```text
gene selected
-> promoter check
-> RNA transcript
-> splice
-> bind to worker
-> produce artifact fragment
-> immune inspect
-> validate
-> promote or quarantine
```

This keeps product growth traceable from original gene to delivered artifact.

## 9. Simulated Bacteria And Immune Hardening

Bacteria are deterministic adversarial fixtures. They simulate product threats without performing real harmful behavior.

Bacteria may inject:

- malformed transcripts;
- contradictory genes;
- rogue plasmids;
- fake completion markers;
- invalid lineage data;
- missing dependency markers;
- budget-drain toxins;
- audit-tamper attempts represented as inert test data;
- membrane-bypass attempts represented as invalid inputs.

Bacteria may not:

- execute real malware;
- modify files outside the sandbox;
- access credentials;
- use network attacks;
- hide audit events;
- mutate runtime policy directly.

### 9.1 White Blood Cells

White blood cells are defensive workers inside the same turn system.

They inspect tasks, transcripts, artifact fragments, and lineage records. They can quarantine suspicious structures, neutralize known defect patterns, and create immune evidence for future tests.

### 9.2 Immune Memory

An immune response is not complete unless it creates durable memory when appropriate.

Durable memory can be:

- an antibody signature;
- a regression test proposal;
- a stricter promoter condition;
- a blocked plasmid fingerprint;
- a quarantine rule;
- a lineage validation rule.

### 9.3 Hardening Loop

```text
bacteria inject defect
-> white blood cell detects marker
-> structure quarantined or neutralized
-> immune evidence recorded
-> antibody or test proposed
-> generation review accepts stable memory
-> future turns reject the same defect earlier
```

The system hardens only when the response improves future behavior.

## 10. Single Active Organism Standard

BioClaw should standardize on one active product organism at a time.

This does not mean the organism is simple. It means the product focus is singular while many microscopic tasks run inside that product's lifecycle.

The data model should still include `organism_id` on turns, generations, and tasks so future multi-organism support does not require a redesign.

## 11. Runtime Components

The next implementation plan should introduce these conceptual components.

| Component | Duty |
| --- | --- |
| `MicroTask` | One microscopic operation with inputs, expected output, hat, and terminal state |
| `Turn` | Batch of micro-tasks plus a strict terminal barrier |
| `TurnEngine` | Assigns tasks, records terminal states, closes turns |
| `Generation` | Group of closed turns under one evolution checkpoint |
| `GenerationEngine` | Reviews generation outputs and creates next-generation proposals |
| `MoleculeRegistry` | Stores DNA, genes, promoters, transcripts, plasmids, antigens, antibodies |
| `PathogenFixture` | Deterministic bacteria fixture that injects inert defects |
| `ImmuneSystem` | Coordinates white blood cell detection, quarantine, neutralization, and memory |
| `AgentHatPolicy` | Defines allowed operations per hat |

## 12. Data Contracts

### 12.1 Turn Record

```yaml
turn:
  turn_id: turn_000001
  generation_id: gen_000001
  organism_id: organism_000001
  status: closed
  task_ids:
    - task_000001
    - task_000002
  terminal_counts:
    complete: 1
    failed: 0
    blocked: 0
    quarantined: 1
  outputs:
    - transcript.auth.password_policy.v1
  immune_events:
    - immune_event_000001
  next_turn_proposals:
    - task_proposal_000003
```

### 12.2 Generation Record

```yaml
generation:
  generation_id: gen_000001
  organism_id: organism_000001
  status: reviewed
  closed_turns:
    - turn_000001
    - turn_000002
  promoted_structures:
    - gene.auth.password_policy
    - antibody.fake_completion_marker
  quarantined_structures:
    - plasmid.injected.fake_done.v1
  next_generation_seed:
    accepted_genes:
      - gene.auth.password_policy
    immune_memory:
      - antibody.fake_completion_marker
```

## 13. Error Handling

The system should treat uncertainty as data.

- If an input is missing, the task becomes `blocked`.
- If an operation runs and cannot produce the expected output, the task becomes `failed`.
- If a structure carries a defect or hostile marker, the task becomes `quarantined`.
- If a task succeeds, it becomes `complete`.

No task may remain `running`, `pending`, or `unknown` after the turn barrier closes.

## 14. Testing Requirements

The first implementation plan should test:

- a turn cannot close with non-terminal tasks;
- a turn closes when all tasks are terminal;
- blocked, failed, and quarantined tasks are preserved as evidence;
- generation review reads only closed turns;
- generation review promotes stable outputs;
- bacteria fixtures inject inert defects;
- white blood cells quarantine known defect markers;
- immune memory records accepted antibodies;
- repeated bacteria attacks are caught earlier after memory exists;
- agent hats cannot perform operations outside their policy.

## 15. Safety Boundaries

This design keeps the existing BioScaffold safety boundaries and adds these rules:

- bacteria are fixtures, not live hostile code;
- injected defects are inert data;
- immune responses cannot delete evidence;
- generation review cannot silently modify policy;
- promotion creates proposals or accepted simulator state only;
- product delivery remains an explicit lifecycle transition, not an autonomous deployment.

## 16. Acceptance Criteria For This Spec

This spec is acceptable when:

- it makes microscopic work the source of macroscopic product growth;
- it defines strict turn barriers with terminal task states;
- it defines generations as review checkpoints over completed turns;
- it targets DNA/RNA-level structures without atom-level modeling;
- it models bacteria and white blood cells as safe deterministic hardening fixtures;
- it keeps one active product organism as the standard;
- it keeps agents focused on simple hat-scoped tasks;
- it is ready to become an implementation plan after user review.
