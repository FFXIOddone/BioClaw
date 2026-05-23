# BioClaw Seeded Autonomous Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe seed-driven BioClaw workflow that can inspect a local project, generate bounded microtasks, run generations to terminal state, checkpoint evidence, and launch OddDB through the OpenClaw-facing CLI.

**Architecture:** Add a deterministic seed layer around the existing autonomous session runner. The seed layer parses a high-level project seed, plans one generation at a time from local repo facts, delegates execution to `AutonomousSessionController`, and stops on completion, policy denial, verification failure, timeout, or generation limit. Safety hardening comes first: dirty-start checks and commit staging must prevent unrelated files or `.bioclaw/` checkpoints from being committed.

**Tech Stack:** Python 3.12, dataclasses, pathlib, subprocess/git CLI, json, pytest, existing BioClaw CLI.

---

## File Structure

- Modify `bioscaffold/autonomy.py`
  - Add dirty-start enforcement.
  - Exclude `.bioclaw/` checkpoint files from commit staging.
  - Add seed request, seed generation record, seed workflow record, seed planner, and seed controller.
- Modify `bioscaffold/cli.py`
  - Add `run-seed` command.
- Modify `bioscaffold/__init__.py`
  - Export seeded workflow public types.
- Modify `tests/test_autonomous_session.py`
  - Add dirty-start, commit-staging, seed planner, and seed controller tests.
- Modify `tests/test_cli.py`
  - Add `run-seed` CLI tests.
- Modify `tests/test_component_cards.py`
  - Add seed type exports to package import expectations.
- Modify `README.md`
  - Document seeded autonomous mode and OddDB seed example.

## Task 1: Safety Hardening Before Seed Runs

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Add failing tests for dirty-start and checkpoint commit exclusion**

Add tests proving:

```python
def test_autonomous_session_blocks_dirty_start_when_not_allowed(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
    request = AutonomousSessionRequest.from_payload({**_request_payload(workspace), "verification_commands": []})

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.BLOCKED
    assert record.task_records == ()
    assert record.commit_refs == ()


def test_autonomous_session_ignores_existing_bioclaw_checkpoint_noise_when_committing(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / ".bioclaw" / "sessions" / "old").mkdir(parents=True)
    (workspace / ".bioclaw" / "sessions" / "old" / "session.json").write_text("{}", encoding="utf-8")
    request = AutonomousSessionRequest.from_payload({
        **_request_payload(workspace),
        "verification_commands": [],
    })

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.COMPLETED
    committed_files = _git(workspace, "show", "--name-only", "--format=", "HEAD").stdout.splitlines()
    assert "README.md" in committed_files
    assert all(not path.startswith(".bioclaw/") for path in committed_files)
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_session_blocks_dirty_start_when_not_allowed .\tests\test_autonomous_session.py::test_autonomous_session_ignores_existing_bioclaw_checkpoint_noise_when_committing -v
```

Expected: dirty-start test currently completes or commits; checkpoint exclusion may commit `.bioclaw/`.

- [ ] **Step 3: Implement safety hardening**

In `AutonomousSessionController.run()`:

- Before project tasks, inspect `git status --porcelain`.
- If `allow_dirty_start` is false, block when dirty entries exist outside `.bioclaw/`.
- Record the dirty check in `command_records`.
- Treat `.bioclaw/` as checkpoint noise, not product work.

In `_commit_if_changed()`:

- Stage only product files, excluding `.bioclaw/`.
- Use `git add -A -- . :!.bioclaw` and verify `git diff --cached --name-only` has staged files before committing.
- If only `.bioclaw/` changed, return completed with no commit.

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py -v
git diff --check
git add .\bioscaffold\autonomy.py .\tests\test_autonomous_session.py
git commit -m "Harden autonomous dirty start commit safety"
```

## Task 2: Seed Request Models and Deterministic Planner

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Add failing tests for seed parsing and planning**

Add tests for:

- `SeedAutonomousRequest.from_payload()` defaults to eight hours and bounded generations.
- `SeedMicrotaskPlanner.plan_generation()` adds `.bioclaw/` to `.gitignore` when missing.
- Planner chooses safe verification commands from the request or from repo facts.
- Planner returns terminal/no-work generation when `.bioclaw/` is already ignored and baseline command exists.

- [ ] **Step 2: Run tests and confirm missing symbols**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py -k "seed" -v
```

Expected: imports fail for missing seed types.

- [ ] **Step 3: Implement seed types**

Add:

- `SeedGenerationStatus`: `planned`, `completed`, `blocked`, `policy_denied`, `timeout`, `generation_limit_reached`.
- `SeedAutonomousRequest`
  - `session_id`
  - `workspace_path`
  - `organism_id`
  - `product_name`
  - `seed_goal`
  - `verification_commands`
  - `max_runtime_seconds=28800`
  - `generation_limit=4`
  - `allow_local_edits=True`
  - `allow_local_commits=True`
  - `allow_push=False`
  - `allow_dirty_start=False`
- `SeedGenerationRecord`
- `SeedAutonomousRecord`
- `SeedMicrotaskPlanner`

Planner behavior:

- Read `.gitignore`, `README.md`, `pyproject.toml`, and `tests/` existence.
- If `.gitignore` exists and lacks `.bioclaw/`, emit one `WRITE_FILE` task that appends `.bioclaw/`.
- If `.gitignore` is missing, emit one `WRITE_FILE` task that creates it with `.bioclaw/`.
- Always include one safe baseline command task:
  - `python -m pytest -q` when `tests/` exists.
  - otherwise `python -c "print('no tests discovered')"`
- Verification commands come from request if provided; otherwise match the baseline command.

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py -k "seed" -v
python -m pytest .\tests\test_autonomous_session.py -v
git diff --check
git add .\bioscaffold\autonomy.py .\tests\test_autonomous_session.py
git commit -m "Add seeded autonomous request planner"
```

## Task 3: Seed Workflow Controller

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Add failing controller tests**

Add tests proving:

- `SeedAutonomousController().run(seed_request)` runs at least one generation and writes `.bioclaw/seeds/<session_id>/seed-session.json`.
- It stops at terminal completed state when planner has no further work.
- It stops with `generation_limit_reached` when work remains but the limit is exhausted.
- It propagates `policy_denied`, `blocked`, and `timeout` statuses from the inner autonomous session.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py -k "seed_autonomous_controller" -v
```

Expected: missing controller and record behavior.

- [ ] **Step 3: Implement controller**

Add `SeedAutonomousController`:

- For each generation from `1..generation_limit`:
  - Ask `SeedMicrotaskPlanner` for generation work.
  - If planner reports no work, finish completed.
  - Convert planned work into `AutonomousSessionRequest` with session id `<seed_session_id>_gNNNNNN`.
  - Delegate to `AutonomousSessionController().run()`.
  - Append `SeedGenerationRecord`.
  - Stop on non-completed inner status.
  - Re-plan after each generation so `.gitignore` changes affect later generations.
- Write seed summary JSON to `.bioclaw/seeds/<session_id>/seed-session.json`.
- Include generation record payloads and inner checkpoint paths.

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py -k "seed" -v
python -m pytest .\tests\test_autonomous_session.py -v
git diff --check
git add .\bioscaffold\autonomy.py .\tests\test_autonomous_session.py
git commit -m "Add seeded autonomous workflow controller"
```

## Task 4: CLI, Public Exports, and README

**Files:**
- Modify: `bioscaffold/cli.py`
- Modify: `bioscaffold/__init__.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_component_cards.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing tests**

Add CLI test:

```python
def test_run_seed_command_runs_seeded_workflow(tmp_path, capsys):
    workspace = tmp_path / "project"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "bioclaw@example.local"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "BioClaw"], cwd=workspace, check=True)
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    request_path = tmp_path / "seed.json"
    request_path.write_text(json.dumps({...}), encoding="utf-8")

    exit_code = main(["run-seed", str(request_path), "--pretty"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"
```

Add exports to `test_package_imports`.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest .\tests\test_cli.py::test_run_seed_command_runs_seeded_workflow .\tests\test_component_cards.py::test_package_imports -v
```

- [ ] **Step 3: Implement CLI and exports**

- Add `run-seed <request> [--pretty]`.
- Parse with `_read_json_object`.
- Call `SeedAutonomousRequest.from_payload()` and `SeedAutonomousController().run()`.
- Print `SeedAutonomousRecord.to_payload()`.
- Export seed types in `bioscaffold/__init__.py`.

- [ ] **Step 4: Update README**

Document:

```powershell
python -m bioscaffold run-seed .\seed-request.json --pretty
```

Include a minimal OddDB seed example and explain:

- seed runs are bounded by `generation_limit` and `max_runtime_seconds`;
- policy still denies push/deploy/install/destructive/secret/out-of-workspace commands;
- `.bioclaw/` checkpoint output is excluded from product commits.

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest .\tests\test_cli.py .\tests\test_component_cards.py::test_package_imports .\tests\test_autonomous_session.py -v
git diff --check
git add .\bioscaffold\cli.py .\bioscaffold\__init__.py .\tests\test_cli.py .\tests\test_component_cards.py .\README.md
git commit -m "Expose seeded autonomous workflow"
```

## Task 5: Final Verification and OddDB Seed Launch

**Files:**
- All implementation files

- [ ] **Step 1: Run full BioClaw verification**

Run:

```powershell
python -m pytest -v
git diff --check
git status --short --branch
```

- [ ] **Step 2: Run real temp-repo seed smoke**

Create a temp Git repo with a trivial pytest test and a seed request, then run:

```powershell
python -m bioscaffold run-seed <seed-request.json> --pretty
python -m bioscaffold session-status <inner-generation-session.json> --pretty
```

Expected:

- seed status `completed`;
- seed summary exists;
- `.bioclaw/` is not in committed file names;
- generated commit contains only product files such as `.gitignore`.

- [ ] **Step 3: Commit or push remaining changes**

If all code is committed, push:

```powershell
git push origin main
```

- [ ] **Step 4: Seed OddDB through OpenClaw**

Create a seed request under temp or `OddDB\.bioclaw\requests\`:

```json
{
  "session_id": "seed_odddb_<timestamp>",
  "workspace_path": "C:/Users/jakeb/Projects/OddDB",
  "organism_id": "organism_odddb_000001",
  "product_name": "OddDB Autonomous Baseline",
  "seed_goal": "Prepare OddDB for safe unattended BioClaw runs and verify its baseline quality.",
  "generation_limit": 3,
  "verification_commands": [
    "python -m odddb --version",
    "python -m odddb doctor --json",
    "python -m unittest discover -v"
  ]
}
```

Run:

```powershell
python -m bioscaffold run-seed <OddDB seed request> --pretty
```

Expected:

- seed status `completed`;
- `.gitignore` includes `.bioclaw/`;
- OddDB tests pass;
- local commit exists only if `.gitignore` needed the checkpoint ignore entry;
- no push from OddDB.

## Self-Review

- The plan addresses unattended safety before adding seed generation.
- The seed planner is deterministic and bounded; it does not invent arbitrary commands.
- Existing `run-session` remains supported.
- OddDB launch uses local verification commands only and no cross-repo writes.
