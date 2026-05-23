# BioClaw Whole-System Fleet Turns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every BioClaw turn emulate a whole biological system fleet where each biological structure performs one small mechanical project action and the turn aggregates the full organism state.

**Architecture:** BioClaw gets a deterministic fleet manifest with at least one worker for each major biological structure layer: genome/DNA, RNA/transcription, protein/ribosome, membrane, mitochondria, immune white blood cell, bacteria/pathogen, tissue, organ, organism memory, and generation reviewer. Each seed generation plans and records per-structure fleet actions, while the existing autonomous session controller still executes only the safe runnable project work items for this first slice. OpenClaw remains the visible cron owner; each cron turn invokes BioClaw once, and BioClaw records the whole-system biological tick inside the turn before later slices fan those structures into separate OpenClaw exec calls.

**Execution status:** Implemented. Reviewer hardening changed Task 3 so BioClaw owns the default fleet manifest; OpenClaw only enables fleet mode and reports the resulting fleet action count.

**Tech Stack:** Python dataclasses and enums in BioClaw, pytest, existing BioClaw CLI, PowerShell OpenClaw runner scripts, JSON seed-session reports.

---

## File Structure

- Modify `bioscaffold/autonomy.py`: add fleet dataclasses/enums, request fields, serialization, parsing, default fleet manifest, and controller aggregation.
- Modify `bioscaffold/__init__.py`: export the new fleet types.
- Modify `tests/test_autonomous_session.py`: add failing tests for manifest defaults, per-generation fleet records, resume parsing, and disabled compatibility.
- Modify `README.md`: document whole-system fleet turns.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSeedTurn.ps1`: enable BioClaw fleet mode, preserve existing state counts when no seed result is produced, and summarize fleet counts.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`: assert OpenClaw turn requests enable fleet mode and expose fleet counts.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\docs\openclaw\bioclaw-tokenless-runner.md`: document the current one-command OpenClaw turn and the BioClaw whole-system fleet inside it.

## Task 1: BioClaw Fleet State Model

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Modify: `bioscaffold/__init__.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write the failing manifest test**

Add this test near the existing seed request/planner tests:

```python
def test_seed_autonomous_request_defaults_to_whole_system_fleet(tmp_path):
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(tmp_path),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )

    manifest = request.structure_fleet
    assert request.enable_structure_fleet is True
    assert len(manifest) >= 11
    assert {unit.structure_type for unit in manifest} >= {
        "dna",
        "rna",
        "protein",
        "membrane",
        "mitochondria",
        "bacteria",
        "white_blood_cell",
        "tissue",
        "organ",
        "organism",
        "generation_reviewer",
    }
    assert all(unit.exec_slot >= 1 for unit in manifest)
    assert all(unit.mechanical_function for unit in manifest)
```

- [ ] **Step 2: Verify the manifest test fails**

Run:

```powershell
python -m pytest tests/test_autonomous_session.py::test_seed_autonomous_request_defaults_to_whole_system_fleet -q
```

Expected: fail because `enable_structure_fleet` and `structure_fleet` do not exist.

- [ ] **Step 3: Implement fleet types and defaults**

In `bioscaffold/autonomy.py`, add:

```python
@dataclass(frozen=True)
class BiologicalFleetUnit:
    unit_id: str
    structure_type: str
    biological_action: str
    mechanical_function: str
    exec_slot: int = 1

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "structure_type": self.structure_type,
            "biological_action": self.biological_action,
            "mechanical_function": self.mechanical_function,
            "exec_slot": self.exec_slot,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BiologicalFleetUnit":
        exec_slot = _optional_int(payload, "exec_slot", 1)
        if exec_slot <= 0:
            raise ValueError("exec_slot must be greater than zero")
        return cls(
            unit_id=_required_string(payload, "unit_id", "structure_fleet[]"),
            structure_type=_required_string(payload, "structure_type", "structure_fleet[]"),
            biological_action=_required_string(payload, "biological_action", "structure_fleet[]"),
            mechanical_function=_required_string(payload, "mechanical_function", "structure_fleet[]"),
            exec_slot=exec_slot,
        )
```

Add `_default_biological_fleet()` returning one unit each for the eleven structures in Step 1. Add `enable_structure_fleet: bool = True` and `structure_fleet: tuple[BiologicalFleetUnit, ...] = ()` to `SeedAutonomousRequest`, parsing `structure_fleet` from JSON or using `_default_biological_fleet()`.

- [ ] **Step 4: Export the fleet type**

In `bioscaffold/__init__.py`, import and add `BiologicalFleetUnit` to `__all__`.

- [ ] **Step 5: Verify Task 1**

Run:

```powershell
python -m pytest tests/test_autonomous_session.py::test_seed_autonomous_request_defaults_to_whole_system_fleet -q
```

Expected: pass.

## Task 2: Per-Generation Fleet Records

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write the failing generation record test**

Add this test near `test_seed_autonomous_controller_resumes_existing_seed_summary_for_generation_batches`:

```python
def test_seed_generation_records_whole_system_fleet_actions(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / ".gitignore").write_text(".bioclaw/\n", encoding="utf-8")
    _git(workspace, "add", ".gitignore")
    _git(workspace, "commit", "-m", "Baseline ignored checkpoints")
    clock = FakeClock()
    session_controller = AdvancingCompletedSessionController(clock=clock, seconds_per_run=1.0)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "verification_commands": ("python -c \"print('verify')\"",),
            "resume_existing_seed": True,
            "generation_batch_size": 1,
            "run_until_runtime_exhausted": True,
            "allow_dirty_start": True,
        }
    )

    record = SeedAutonomousController(
        session_controller=session_controller,
        clock=clock.monotonic,
        sleep=clock.sleep,
    ).run(request)

    generation = record.generations[0]
    assert len(generation.fleet_actions) == len(request.structure_fleet)
    assert {action.structure_type for action in generation.fleet_actions} >= {
        "dna",
        "rna",
        "bacteria",
        "white_blood_cell",
        "organism",
    }
    assert all(action.status == "planned" for action in generation.fleet_actions)
    payload = json.loads(
        (workspace / ".bioclaw" / "seeds" / request.session_id / "seed-session.json").read_text(encoding="utf-8")
    )
    assert len(payload["generations"][0]["fleet_actions"]) == len(request.structure_fleet)
```

- [ ] **Step 2: Verify the generation record test fails**

Run:

```powershell
python -m pytest tests/test_autonomous_session.py::test_seed_generation_records_whole_system_fleet_actions -q
```

Expected: fail because `fleet_actions` does not exist.

- [ ] **Step 3: Implement fleet action records**

In `bioscaffold/autonomy.py`, add:

```python
@dataclass(frozen=True)
class BiologicalFleetActionRecord:
    unit_id: str
    structure_type: str
    biological_action: str
    mechanical_function: str
    status: str = "planned"
    evidence: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "structure_type": self.structure_type,
            "biological_action": self.biological_action,
            "mechanical_function": self.mechanical_function,
            "status": self.status,
            "evidence": self.evidence,
        }
```

Add `fleet_actions: tuple[BiologicalFleetActionRecord, ...] = ()` to `SeedGenerationPlan` and `SeedGenerationRecord`. `SeedMicrotaskPlanner.plan_generation()` should attach `_fleet_actions_for_generation(request, generation_index)` when `request.enable_structure_fleet` is true. All `SeedGenerationRecord(...)` creation sites must copy `plan.fleet_actions`.

- [ ] **Step 4: Parse fleet actions on resume**

Update `_seed_generation_record_from_payload()` to parse `fleet_actions` back into `BiologicalFleetActionRecord` objects.

- [ ] **Step 5: Verify Task 2**

Run:

```powershell
python -m pytest tests/test_autonomous_session.py::test_seed_generation_records_whole_system_fleet_actions tests/test_autonomous_session.py::test_seed_autonomous_controller_resumes_existing_seed_summary_for_generation_batches -q
```

Expected: both pass.

## Task 3: OpenClaw Fleet Mode And Reporting

**Files:**
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSeedTurn.ps1`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`

- [ ] **Step 1: Write the failing OpenClaw dry-run assertions**

In `Test-FfxiOpenClawBioClawSeed.ps1`, add assertions after the turn dry-run request assertions:

```powershell
Assert-Equal $true $turnDry.request.enable_structure_fleet 'turn runner should enable BioClaw whole-system fleet mode'
Assert-True ($turnDry.request.PSObject.Properties.Name -notcontains 'structure_fleet') 'turn runner should let BioClaw own the default biological fleet manifest'
Assert-Equal 0 $turnDry.fleetActionCount 'turn runner dry-run should expose fleet action count before execution'
```

- [ ] **Step 2: Verify the OpenClaw test fails**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: fail because the turn request does not enable fleet mode or expose fleet action counts.

- [ ] **Step 3: Add fleet mode to turn requests**

In `Invoke-FfxiOpenClawBioClawSeedTurn.ps1`, add `enable_structure_fleet = $true` to the seed request. Do not pass `structure_fleet` from OpenClaw; BioClaw owns the default manifest to avoid drift between PowerShell and Python.

- [ ] **Step 4: Add fleet count summary and state preservation**

In `Invoke-FfxiOpenClawBioClawSeedTurn.ps1`, initialize `generationCount` and `fleetActionCount` from existing `turn-state.json` so dry runs, skipped locks, and failures do not clobber prior progress. When a seed result exists, calculate:

```powershell
$fleetActionCount = 0
if ($null -ne $seedResult -and $seedResult.PSObject.Properties.Name -contains 'generations') {
    $latestGeneration = @($seedResult.generations) | Select-Object -Last 1
    if ($null -ne $latestGeneration -and $latestGeneration.PSObject.Properties.Name -contains 'fleet_actions') {
        $fleetActionCount = @($latestGeneration.fleet_actions).Count
    }
}
```

Add `fleetActionCount` to state and summary JSON. Also make stdout JSON parsing tolerant of warning text around the JSON object.

- [ ] **Step 5: Verify Task 3**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: pass.

## Task 4: Docs And End-To-End Verification

**Files:**
- Modify: `README.md`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\docs\openclaw\bioclaw-tokenless-runner.md`

- [ ] **Step 1: Document the current fleet model**

Add that each cron run currently performs one OpenClaw foreground command, and inside that command BioClaw executes a whole-system fleet tick with one action per biological structure. State that a later OpenClaw fan-out slice will split each structure into its own exec while preserving the same state schema.

- [ ] **Step 2: Run full BioClaw tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Run OpenClaw runner tests**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
.\tools\openclaw\Test-FfxiOpenClawAutonomy.ps1
.\tools\openclaw\Test-FfxiOpenClawQueuePump.ps1
```

Expected: all tests pass.

- [ ] **Step 4: Launch one short visible OpenClaw fleet turn**

Run:

```powershell
.\tools\openclaw\Invoke-FfxiOpenClawBioClawSession.ps1 -TurnDelaySeconds 60 -TurnRuntimeSeconds 300 -Json
```

Expected: OpenClaw creates a cron job, the first turn completes with `status = paused`, `fleetActionCount >= 11`, `requestHasStructureFleet = false`, and no long-running child process remains between turns.

- [ ] **Step 5: Commit scoped changes**

BioClaw repo:

```powershell
git add README.md bioscaffold/autonomy.py bioscaffold/__init__.py tests/test_autonomous_session.py docs/superpowers/plans/2026-05-23-bioclaw-whole-system-fleet-turns.md
git commit -m "Add whole-system biological fleet turns"
```

Parent workspace repo:

```powershell
git add -- "FFXI Personal Server/tools/openclaw/Invoke-FfxiOpenClawBioClawSeedTurn.ps1" "FFXI Personal Server/tools/openclaw/Test-FfxiOpenClawBioClawSeed.ps1" "FFXI Personal Server/docs/openclaw/bioclaw-tokenless-runner.md"
git commit -m "Pass BioClaw fleet turns through OpenClaw"
```

## Self-Review

- Spec coverage: Covers the requested difference from one exec/one generation to a whole-system biological fleet per turn, with a staged path to later per-structure OpenClaw exec fan-out.
- Placeholder scan: No placeholders or deferred task descriptions are present; each task has concrete files, commands, and expected outcomes.
- Type consistency: `BiologicalFleetUnit`, `BiologicalFleetActionRecord`, `enable_structure_fleet`, `structure_fleet`, and `fleet_actions` are named consistently. OpenClaw intentionally sends only `enable_structure_fleet`; BioClaw owns `structure_fleet`.
