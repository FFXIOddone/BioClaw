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

## Planning Artifacts

- Design spec: `docs/superpowers/specs/2026-05-22-bioscaffold-os-design.md`
- Foundation implementation plan: `docs/superpowers/plans/2026-05-22-bioscaffold-os-foundation.md`
