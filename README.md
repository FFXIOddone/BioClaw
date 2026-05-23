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

## OpenClaw Runnable Entry Point

BioScaffold exposes a noninteractive product workflow command that OpenClaw can call from the workspace:

```powershell
python -m bioscaffold run-product .\request.json --output .\delivery-report.json
```

Minimal request:

```json
{
  "organism_id": "organism_000001",
  "product_name": "Authentication Module",
  "requirements": [
    {
      "requirement_id": "password-policy",
      "text": "Require password policy.",
      "artifact_type": "code"
    }
  ]
}
```

If `--output` is omitted, the delivery report JSON is written to stdout. Reports include the terminal state, archive ref, generation IDs, task IDs, validation refs, assembly refs, immune events, and project microtask count.

### Autonomous Session Mode

For local-only autonomous project work:

```powershell
python -m bioscaffold run-session .\autonomous-request.json --pretty
python -m bioscaffold session-status .\.bioclaw\sessions\<session_id>\session.json --pretty
python -m bioscaffold resume-session .\.bioclaw\sessions\<session_id>\session.json --pretty
```

The default runtime budget is eight hours. Autonomous mode allows local file edits, local verification commands, checkpoint writes, and local commits. By default, it denies:

- push
- deploy
- publish
- install
- destructive commands (for example, deletion or recursive removal)
- secret reads
- commands that target paths outside the workspace

### Seeded Autonomous Mode

For seeded workflows, pass a seed request to launch bounded generation cycles and write the summary to `.bioclaw/seeds/<session_id>/seed-session.json`:

```powershell
python -m bioscaffold run-seed .\seed-request.json --pretty
```

Minimal OddDB seed request example:

```json
{
  "session_id": "seed_odddb_000001",
  "workspace_path": "C:/Users/jakeb/Projects/OddDB",
  "organism_id": "organism_odddb_000001",
  "product_name": "OddDB Autonomous Baseline",
  "seed_goal": "Prepare OddDB for safe unattended BioClaw runs and verify baseline quality.",
  "generation_limit": 3,
  "verification_commands": [
    "python -m odddb --version",
    "python -m odddb doctor --json",
    "python -m unittest discover -v"
  ]
}
```

Seeded runs are bounded by:

- `generation_limit` (stop after the configured number of microtask generations),
- `max_runtime_seconds` (session runtime limit for each inner autonomous session).

For full endurance runs, set:

```json
{
  "run_until_runtime_exhausted": true,
  "turn_delay_seconds": 60,
  "generation_limit": 10000,
  "max_runtime_seconds": 28800
}
```

In this mode a terminal/no-work repository does not stop immediately. BioClaw converts terminal state into verification-only generations and keeps running turn after turn until the wall-clock budget is exhausted, a safety policy blocks execution, verification fails, or the generation ceiling is reached.

For scheduler-owned runs, split the burn into resumable one-generation batches:

```json
{
  "resume_existing_seed": true,
  "generation_batch_size": 1,
  "run_until_runtime_exhausted": true,
  "turn_delay_seconds": 0
}
```

With these fields, repeated `run-seed` invocations append to `.bioclaw/seeds/<session_id>/seed-session.json`. Each batch returns `status = "paused"` until the generation limit, a policy failure, or the external scheduler's wall-clock deadline ends the run. Terminal/no-work repositories become verification-only generations, so the scheduler can keep burning without one long process.

Each seeded generation now records a whole-system biological fleet by default. The default fleet includes DNA, RNA, protein, membrane, mitochondria, bacteria, white blood cell, tissue, organ, organism, and generation-reviewer structures. Every structure records one tiny biological action mapped to a mechanical project function in `generations[].fleet_actions`; the runnable project work remains bounded and policy-checked through the existing autonomous session executor.

OpenClaw fleet-turn orchestration reads that same default manifest through:

```powershell
python -m bioscaffold fleet-manifest --pretty
```

The manifest command is the source of truth for scheduler integrations. OpenClaw uses it to create one command file per biological structure plus one fleet-turn orchestrator command file. Each OpenClaw cron turn runs that orchestrator once with a foreground `exec`; the orchestrator records every structure-level action, then runs one final command for the safe BioClaw generation. That keeps the local tokenless OpenClaw agent on one reliable tool call per turn while still producing a visible per-structure fleet ledger.

Seeded workflow inherits existing autonomous policy defaults:

- push is denied unless explicitly allowed,
- deploy/publish/install/destructive/path-escape/secret reads are denied,
- command/path constraints apply to every inner run.

Checkpoint data under `.bioclaw/` is excluded from product commits so it is not shipped as product changes.

## Planning Artifacts

- Design spec: `docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md`
- Foundation implementation plan: `docs/superpowers/plans/2026-05-22-bioscaffold-os-foundation.md`
