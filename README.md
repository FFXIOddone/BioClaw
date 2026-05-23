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
