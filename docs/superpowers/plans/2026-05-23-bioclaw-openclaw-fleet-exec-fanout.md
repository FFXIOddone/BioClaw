# BioClaw OpenClaw Fleet Exec Fan-Out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each OpenClaw cron turn run a visible fleet of biological structure actions before the final BioClaw generation, while keeping the tokenless OpenClaw agent on one reliable foreground `exec` call per turn.

**Architecture:** BioClaw remains the source of truth for the biological fleet manifest through a new CLI command. The OpenClaw session launcher reads that manifest, writes one tiny command file per fleet unit, writes one fleet-turn orchestrator command file, and prompts OpenClaw to execute that orchestrator once. The orchestrator calls each fleet unit command in order, then calls the existing seed turn command. A new fleet-unit runner appends per-structure JSONL ledger records; the final seed turn reports both BioClaw `fleetActionCount` and OpenClaw `openClawFleetExecCount`.

**Implementation note:** The original direct fan-out design asked tokenless OpenClaw to perform one tool call per fleet unit. A smoke run showed the local agent stopped after six `exec` calls and summarized success early. The implemented runnable design therefore keeps OpenClaw to one foreground `exec` per turn and moves the per-unit fan-out into the generated command file.

**Tech Stack:** Python argparse/pytest in BioClaw, PowerShell OpenClaw runner scripts, JSON/JSONL report files, native OpenClaw cron foreground `exec`.

---

## File Structure

- Modify `bioscaffold/autonomy.py`: expose `default_biological_fleet()` as the public manifest source.
- Modify `bioscaffold/cli.py`: add `fleet-manifest` command.
- Modify `bioscaffold/__init__.py`: export `default_biological_fleet`.
- Modify `tests/test_cli.py`: test `fleet-manifest`.
- Modify `tests/test_component_cards.py`: update public exports.
- Create `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawFleetUnit.ps1`: record one biological structure's tiny OpenClaw exec action.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSeedTurn.ps1`: accept fleet ledger path and report OpenClaw fleet exec counts.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSession.ps1`: fetch BioClaw manifest, write per-unit command files, write the fleet-turn orchestrator, and prompt OpenClaw to run that orchestrator once.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`: test fleet-unit runner, session dry-run command files, prompt, and count preservation.
- Modify `C:\Users\jakeb\Projects\FFXI Personal Server\docs\openclaw\bioclaw-tokenless-runner.md`: document fleet-turn orchestration.
- Modify `README.md`: document `fleet-manifest` and OpenClaw orchestration role.

## Task 1: BioClaw Fleet Manifest CLI

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Modify: `bioscaffold/cli.py`
- Modify: `bioscaffold/__init__.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_component_cards.py`

- [ ] **Step 1: Write the failing CLI test**

Add this test to `tests/test_cli.py`:

```python
def test_fleet_manifest_command_outputs_default_structure_fleet(capsys):
    exit_code = main(["fleet-manifest", "--pretty"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["enable_structure_fleet"] is True
    assert payload["fleet_count"] >= 11
    assert len(payload["structure_fleet"]) == payload["fleet_count"]
    assert {unit["structure_type"] for unit in payload["structure_fleet"]} >= {
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
```

- [ ] **Step 2: Verify the CLI test fails**

Run:

```powershell
python -m pytest tests/test_cli.py::test_fleet_manifest_command_outputs_default_structure_fleet -q
```

Expected: fail because `fleet-manifest` is not a known command.

- [ ] **Step 3: Expose the default fleet manifest**

In `bioscaffold/autonomy.py`, add:

```python
def default_biological_fleet() -> tuple[BiologicalFleetUnit, ...]:
    return _default_biological_fleet()
```

In `bioscaffold/__init__.py`, import and export `default_biological_fleet`.

- [ ] **Step 4: Add the CLI command**

In `bioscaffold/cli.py`, import `default_biological_fleet`, add a subparser named `fleet-manifest` with `--pretty`, and route it from `main()`:

```python
if args.command == "fleet-manifest":
    return _fleet_manifest(args)
```

Implement:

```python
def _fleet_manifest(args: argparse.Namespace) -> int:
    fleet = default_biological_fleet()
    _print_json(
        {
            "enable_structure_fleet": True,
            "fleet_count": len(fleet),
            "structure_fleet": [unit.to_payload() for unit in fleet],
        },
        pretty=args.pretty,
    )
    return 0
```

- [ ] **Step 5: Verify Task 1**

Run:

```powershell
python -m pytest tests/test_cli.py::test_fleet_manifest_command_outputs_default_structure_fleet tests/test_component_cards.py::test_package_imports -q
```

Expected: pass.

## Task 2: OpenClaw Fleet Unit Runner

**Files:**
- Create: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawFleetUnit.ps1`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`

- [ ] **Step 1: Write the failing PowerShell test**

In `Test-FfxiOpenClawBioClawSeed.ps1`, add `$fleetUnitRunnerPath = Join-Path $PSScriptRoot 'Invoke-FfxiOpenClawBioClawFleetUnit.ps1'`, assert it exists, then add this test block after the turn dry-run block:

```powershell
$fleetLedgerPath = Join-Path $reportRoot 'fleet-ledger.jsonl'
$fleetUnitJson = & $fleetUnitRunnerPath `
    -WorkspacePath $workspacePath `
    -BioClawRoot $bioClawRoot `
    -AllowedProjectsRoot $projectsRoot `
    -ReportRoot $reportRoot `
    -StatePath $turnStatePath `
    -SessionId 'seed_odddb_openclaw_test' `
    -TargetName 'OddDB' `
    -UnitId 'fleet.dna' `
    -StructureType 'dna' `
    -BiologicalAction 'store instructions' `
    -MechanicalFunction 'preserve the seed goal' `
    -FleetLedgerPath $fleetLedgerPath `
    -Json
$fleetUnit = $fleetUnitJson | ConvertFrom-Json
$ledgerLine = Get-Content -LiteralPath $fleetLedgerPath | Select-Object -First 1 | ConvertFrom-Json

Assert-Equal 'recorded' $fleetUnit.status 'fleet unit runner should record the unit action'
Assert-Equal 'fleet.dna' $fleetUnit.unitId 'fleet unit summary should include unit id'
Assert-Equal 1 $fleetUnit.turnNumber 'fleet unit should target the next OpenClaw turn number'
Assert-Equal 'fleet.dna' $ledgerLine.unitId 'fleet ledger should include unit id'
Assert-Equal 'dna' $ledgerLine.structureType 'fleet ledger should include structure type'
```

- [ ] **Step 2: Verify the PowerShell test fails**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: fail because the fleet unit runner script does not exist.

- [ ] **Step 3: Implement the fleet unit runner**

Create `Invoke-FfxiOpenClawBioClawFleetUnit.ps1`. It must:

- validate `WorkspacePath`, `BioClawRoot`, `ReportRoot`, `StatePath`, and `FleetLedgerPath` stay inside allowed roots,
- read existing `turn-state.json` if present,
- preserve `sessionId` from state when present,
- compute `turnNumber = state.turnCount + 1`,
- append one compact JSON object to `fleet-ledger.jsonl`,
- write a per-unit summary JSON under `ReportRoot`,
- return JSON when `-Json` is passed.

The ledger JSON object must include:

```powershell
generatedAt, targetName, sessionId, turnNumber, unitId, structureType,
biologicalAction, mechanicalFunction, execSlot, status
```

- [ ] **Step 4: Verify Task 2**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: pass the new fleet unit runner assertions.

## Task 3: Seed Turn Fleet Ledger Reporting

**Files:**
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSeedTurn.ps1`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`

- [ ] **Step 1: Write failing count-preservation assertions**

Extend the existing preserve-state test object with:

```powershell
openClawFleetExecCount = 11
lastFleetLedgerPath = 'previous-ledger'
```

Add assertions:

```powershell
Assert-Equal 11 $preserveDry.openClawFleetExecCount 'turn runner dry-run should preserve prior OpenClaw fleet exec count'
Assert-Equal 11 $preservedState.openClawFleetExecCount 'turn runner state should not clobber OpenClaw fleet exec count without a seed result'
```

- [ ] **Step 2: Verify the assertions fail**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: fail because the turn runner does not expose `openClawFleetExecCount`.

- [ ] **Step 3: Add ledger path and OpenClaw fleet count**

In `Invoke-FfxiOpenClawBioClawSeedTurn.ps1`, add parameter:

```powershell
[string]$FleetLedgerPath,
```

Default it to `fleet-ledger.jsonl` beside `StatePath`, validate it stays inside the FFXI workspace, initialize `openClawFleetExecCount` from state, and calculate the current turn number before incrementing `turnCount`.

- [ ] **Step 4: Count ledger records for executed turns**

After execution, if the ledger exists, read each JSONL line and count records matching current `sessionId` and `turnNumber`. Add the count to state and summary as `openClawFleetExecCount`, and add `lastFleetLedgerPath`.

- [ ] **Step 5: Verify Task 3**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: pass.

## Task 4: Session Launcher Fleet Fan-Out

**Files:**
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Invoke-FfxiOpenClawBioClawSession.ps1`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1`

- [ ] **Step 1: Write failing session dry-run assertions**

In the session dry-run assertions, add:

```powershell
Assert-True (@($sessionDry.fleetCommandFiles).Count -ge 11) 'session launcher should write one command file per biological fleet unit'
Assert-True (Test-Path -LiteralPath $sessionDry.fleetTurnCommandFile -PathType Leaf) 'session launcher should write the fleet turn orchestrator command file'
Assert-True ($sessionDry.prompt -like '*run the BioClaw fleet turn command file exactly once*') 'session prompt should instruct one reliable foreground exec'
Assert-True ($sessionDry.prompt -like '*run-bioclaw-turn.cmd*') 'session prompt should still describe the final turn command'
Assert-True ($sessionDry.prompt -like '*openClawFleetExecCount*') 'session prompt should ask for fleet exec count'
Assert-True (Test-Path -LiteralPath $sessionDry.fleetLedgerPath -PathType Leaf) 'session launcher should initialize fleet ledger file'
```

Also assert every file path in `fleetCommandFiles` exists and the fleet-turn command file calls the first fleet command, final fleet command, and `run-bioclaw-turn.cmd`.

- [ ] **Step 2: Verify the session dry-run assertions fail**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: fail because the launcher still writes only one final turn command.

- [ ] **Step 3: Fetch the BioClaw fleet manifest**

Add `-PythonExe` to `Invoke-FfxiOpenClawBioClawSession.ps1`. Add a helper that runs:

```powershell
& $PythonExe -m bioscaffold fleet-manifest --pretty
```

with `WorkingDirectory = $BioClawRoot`, parses JSON, validates `structure_fleet` is a non-empty list, and returns the fleet units. The test fake BioClaw root should implement enough `bioscaffold\__main__.py` behavior to print a valid manifest.

- [ ] **Step 4: Write one command file per fleet unit**

For each manifest unit, write `run-bioclaw-fleet-<index>-<safe-unit-name>.cmd` that calls:

```powershell
Invoke-FfxiOpenClawBioClawFleetUnit.ps1 -WorkspacePath <workspace> -BioClawRoot <bioclaw> -AllowedProjectsRoot <projects> -ReportRoot <report> -StatePath <state> -SessionId <session> -TargetName <target> -UnitId <unit> -StructureType <type> -BiologicalAction <action> -MechanicalFunction <function> -ExecSlot <slot> -FleetLedgerPath <ledger> -Json
```

- [ ] **Step 5: Update final turn command, orchestrator, and prompt**

Pass `-FleetLedgerPath <ledger>` and `-PythonExe <python>` to `run-bioclaw-turn.cmd`. Write `run-bioclaw-fleet-turn.cmd` so it calls every fleet command in exact order, stops on the first non-zero exit code, and then calls the final turn command. Replace the prompt with instructions to run only `run-bioclaw-fleet-turn.cmd` using one foreground `exec background=false`, then report `status`, `statePath`, `turnCount`, `generationCount`, `fleetActionCount`, `openClawFleetExecCount`, and exit code.

- [ ] **Step 6: Verify Task 4**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
```

Expected: pass.

## Task 5: Docs, Full Verification, And Live OddDB Launch

**Files:**
- Modify: `README.md`
- Modify: `C:\Users\jakeb\Projects\FFXI Personal Server\docs\openclaw\bioclaw-tokenless-runner.md`

- [ ] **Step 1: Document the finished run model**

Document that each OpenClaw cron turn now executes:

1. one foreground OpenClaw `exec` for the generated fleet-turn command file,
2. one command file per BioClaw biological fleet unit inside that orchestrator,
3. one final command inside that orchestrator for the safe BioClaw generation,
4. one shared turn state file containing both `fleetActionCount` and `openClawFleetExecCount`.

- [ ] **Step 2: Run full BioClaw tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Run OpenClaw tests**

Run:

```powershell
.\tools\openclaw\Test-FfxiOpenClawBioClawSeed.ps1
.\tools\openclaw\Test-FfxiOpenClawAutonomy.ps1
.\tools\openclaw\Test-FfxiOpenClawQueuePump.ps1
```

Expected: all tests pass.

- [ ] **Step 4: Launch a short OpenClaw smoke run**

Run:

```powershell
.\tools\openclaw\Invoke-FfxiOpenClawBioClawSession.ps1 -MaxRuntimeSeconds 180 -GenerationLimit 5 -TurnDelaySeconds 420 -TurnRuntimeSeconds 60 -Json
```

Expected: first turn reaches `status = paused`, `fleetActionCount = 11`, `openClawFleetExecCount = 11`; disable the smoke cron after proof.

- [ ] **Step 5: Launch the real eight-hour OddDB run**

Run:

```powershell
.\tools\openclaw\Invoke-FfxiOpenClawBioClawSession.ps1 -Json
```

Expected: OpenClaw creates an enabled cron session for OddDB. Confirm `openclaw cron list` shows it enabled and the state file exists.

- [ ] **Step 6: Commit scoped changes**

BioClaw:

```powershell
git add README.md bioscaffold/autonomy.py bioscaffold/cli.py bioscaffold/__init__.py tests/test_cli.py tests/test_component_cards.py docs/superpowers/plans/2026-05-23-bioclaw-openclaw-fleet-exec-fanout.md
git commit -m "Expose BioClaw fleet manifest"
git push origin main
```

Parent workspace:

```powershell
git add -- "FFXI Personal Server/tools/openclaw/Invoke-FfxiOpenClawBioClawFleetUnit.ps1" "FFXI Personal Server/tools/openclaw/Invoke-FfxiOpenClawBioClawSeedTurn.ps1" "FFXI Personal Server/tools/openclaw/Invoke-FfxiOpenClawBioClawSession.ps1" "FFXI Personal Server/tools/openclaw/Test-FfxiOpenClawBioClawSeed.ps1" "FFXI Personal Server/docs/openclaw/bioclaw-tokenless-runner.md"
git commit -m "Run BioClaw fleet turn through OpenClaw"
```

## Self-Review

- Spec coverage: Implements the requested fleet of biological structure actions per turn, keeps BioClaw as manifest source of truth, and starts a live OddDB OpenClaw run after verification.
- Placeholder scan: No placeholders or future-only steps remain; each task has exact files, commands, and expected results.
- Type consistency: Uses `fleet-manifest`, `structure_fleet`, `fleetCommandFiles`, `fleetTurnCommandFile`, `fleetLedgerPath`, `fleetActionCount`, and `openClawFleetExecCount` consistently.
