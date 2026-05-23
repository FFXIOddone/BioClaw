# BioClaw Autonomous Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-only autonomous work session runner that can execute bounded project tasks, checkpoint every generation, verify outputs, and create local commits under an eight-hour default runtime budget.

**Architecture:** Add a thin autonomous session layer beside the existing all-generation workflow rather than replacing it. The new layer owns request/session records, policy checks, checkpoint storage, local task execution, verification, and commit gating, while the existing biological workflow remains the conceptual product-growth model.

**Tech Stack:** Python 3.12, dataclasses, `json`, `subprocess`, `pathlib`, pytest, local git CLI.

---

## File Structure

- Create `bioscaffold/autonomy.py`: autonomous request/session dataclasses, policy engine, checkpoint store, executor, controller, and JSON payload helpers.
- Modify `bioscaffold/cli.py`: add `run-session`, `resume-session`, and `session-status` commands.
- Modify `bioscaffold/__init__.py`: export public autonomous session types.
- Modify `README.md`: document the request JSON and CLI commands.
- Create `tests/test_autonomous_session.py`: unit/integration coverage for request defaults, policy denial, checkpointing, resume, verification, timeout, and commit gate.
- Modify `tests/test_cli.py`: CLI coverage for session commands.
- Modify `tests/test_component_cards.py`: update public package export expectations.

## Task 1: Autonomous Request, Status, and Policy Models

**Files:**
- Create: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write failing tests for request defaults and policy denial**

Add to `tests/test_autonomous_session.py`:

```python
import json

from bioscaffold.autonomy import (
    AutonomousOperation,
    AutonomousPolicy,
    AutonomousSessionRequest,
    AutonomousWorkItem,
)


def test_autonomous_request_defaults_to_eight_hour_runtime(tmp_path):
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(tmp_path),
            "organism_id": "organism_000001",
            "product_name": "Authentication Module",
            "requirements": [
                {
                    "requirement_id": "password-policy",
                    "text": "Require password policy.",
                    "artifact_type": "code",
                }
            ],
            "project_tasks": [
                {
                    "task_id": "task.write.readme",
                    "operation": "write_file",
                    "path": "README.md",
                    "content": "# Demo\n",
                }
            ],
            "verification_commands": ["python -c \"print('ok')\""],
        }
    )

    assert request.max_runtime_seconds == 28800
    assert request.generation_limit == 24
    assert request.turn_limit == 96
    assert request.allow_local_edits is True
    assert request.allow_local_commits is True
    assert request.allow_push is False
    assert request.project_tasks[0].operation is AutonomousOperation.WRITE_FILE


def test_autonomous_policy_denies_push_deploy_install_and_destructive_commands(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        AutonomousWorkItem("task.push", AutonomousOperation.RUN_COMMAND, command="git push"),
        AutonomousWorkItem("task.deploy", AutonomousOperation.RUN_COMMAND, command="npm run deploy"),
        AutonomousWorkItem("task.install", AutonomousOperation.RUN_COMMAND, command="pip install requests"),
        AutonomousWorkItem("task.delete", AutonomousOperation.RUN_COMMAND, command="Remove-Item -Recurse ."),
    ]

    for item in denied:
        decision = policy.authorize(item)
        assert decision.allowed is False
        assert decision.reason
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_request_defaults_to_eight_hour_runtime .\tests\test_autonomous_session.py::test_autonomous_policy_denies_push_deploy_install_and_destructive_commands -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'bioscaffold.autonomy'`.

- [ ] **Step 3: Implement minimal models and policy**

Create `bioscaffold/autonomy.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any

from bioscaffold.compiler import ProductRequirement
from bioscaffold.types import PolicyDecision


class AutonomousOperation(str, Enum):
    INSPECT_FILE = "inspect_file"
    WRITE_FILE = "write_file"
    RUN_COMMAND = "run_command"
    VERIFY = "verify"
    GIT_COMMIT = "git_commit"
    RECORD = "record"


class AutonomousSessionStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    POLICY_DENIED = "policy_denied"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class AutonomousWorkItem:
    task_id: str
    operation: AutonomousOperation
    path: str = ""
    content: str = ""
    command: str = ""
    expected_output: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AutonomousWorkItem":
        operation = AutonomousOperation(_required_string(payload, "operation", "project_tasks[]"))
        return cls(
            task_id=_required_string(payload, "task_id", "project_tasks[]"),
            operation=operation,
            path=str(payload.get("path", "")),
            content=str(payload.get("content", "")),
            command=str(payload.get("command", "")),
            expected_output=str(payload.get("expected_output", "")),
        )


@dataclass(frozen=True)
class AutonomousSessionRequest:
    session_id: str
    workspace_path: Path
    organism_id: str
    product_name: str
    requirements: tuple[ProductRequirement, ...]
    project_tasks: tuple[AutonomousWorkItem, ...]
    verification_commands: tuple[str, ...]
    max_runtime_seconds: int = 28800
    generation_limit: int = 24
    turn_limit: int = 96
    allow_local_edits: bool = True
    allow_local_commits: bool = True
    allow_push: bool = False
    allow_dirty_start: bool = False

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AutonomousSessionRequest":
        requirements = tuple(
            ProductRequirement(
                requirement_id=_required_string(item, "requirement_id", "requirements[]"),
                text=_required_string(item, "text", "requirements[]"),
                artifact_type=str(item.get("artifact_type", "code")),
                markers=tuple(item.get("markers", ())),
            )
            for item in _required_list(payload, "requirements")
        )
        if not requirements:
            raise ValueError("requirements must contain at least one item")
        project_tasks = tuple(
            AutonomousWorkItem.from_payload(item)
            for item in _required_list(payload, "project_tasks")
        )
        if not project_tasks:
            raise ValueError("project_tasks must contain at least one item")
        return cls(
            session_id=_required_string(payload, "session_id"),
            workspace_path=Path(_required_string(payload, "workspace_path")).resolve(),
            organism_id=_required_string(payload, "organism_id"),
            product_name=_required_string(payload, "product_name"),
            requirements=requirements,
            project_tasks=project_tasks,
            verification_commands=tuple(str(command) for command in payload.get("verification_commands", ())),
            max_runtime_seconds=int(payload.get("max_runtime_seconds", 28800)),
            generation_limit=int(payload.get("generation_limit", 24)),
            turn_limit=int(payload.get("turn_limit", 96)),
            allow_local_edits=bool(payload.get("allow_local_edits", True)),
            allow_local_commits=bool(payload.get("allow_local_commits", True)),
            allow_push=bool(payload.get("allow_push", False)),
            allow_dirty_start=bool(payload.get("allow_dirty_start", False)),
        )


@dataclass(frozen=True)
class AutonomousTaskRecord:
    task_id: str
    operation: AutonomousOperation
    state: str
    reason: str
    path: str = ""
    command: str = ""
    outputs: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "operation": self.operation.value,
            "state": self.state,
            "reason": self.reason,
            "path": self.path,
            "command": self.command,
            "outputs": list(self.outputs),
        }


@dataclass(frozen=True)
class CommandRecord:
    command: str
    exit_code: int
    stdout: str
    stderr: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class AutonomousSessionRecord:
    session_id: str
    workspace_path: str
    organism_id: str
    product_name: str
    status: AutonomousSessionStatus
    max_runtime_seconds: int
    generation_index: int = 0
    task_records: tuple[AutonomousTaskRecord, ...] = ()
    command_records: tuple[CommandRecord, ...] = ()
    commit_refs: tuple[str, ...] = ()
    checkpoint_dir: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "workspace_path": self.workspace_path,
            "organism_id": self.organism_id,
            "product_name": self.product_name,
            "status": self.status.value,
            "max_runtime_seconds": self.max_runtime_seconds,
            "generation_index": self.generation_index,
            "checkpoint_dir": self.checkpoint_dir,
            "task_records": [record.to_payload() for record in self.task_records],
            "command_records": [record.to_payload() for record in self.command_records],
            "commit_refs": list(self.commit_refs),
        }


class AutonomousPolicy:
    def __init__(self, *, workspace_path: Path, allow_push: bool = False) -> None:
        self.workspace_path = workspace_path.resolve()
        self.allow_push = allow_push

    @classmethod
    def default(cls, *, workspace_path: Path, allow_push: bool = False) -> "AutonomousPolicy":
        return cls(workspace_path=workspace_path, allow_push=allow_push)

    def authorize(self, item: AutonomousWorkItem) -> PolicyDecision:
        if item.operation is AutonomousOperation.WRITE_FILE:
            return self._authorize_path(item.path)
        if item.operation is AutonomousOperation.RUN_COMMAND:
            return self._authorize_command(item.command)
        return PolicyDecision.allow("operation allowed")

    def _authorize_path(self, relative_path: str) -> PolicyDecision:
        target = (self.workspace_path / relative_path).resolve()
        if not str(target).startswith(str(self.workspace_path)):
            return PolicyDecision.deny("path escapes workspace")
        return PolicyDecision.allow("path is inside workspace")

    def _authorize_command(self, command: str) -> PolicyDecision:
        lowered = command.lower()
        denied_tokens = (" deploy", " publish", " install", "remove-item", " rm ", " rmdir ", "del ")
        if "git push" in lowered and not self.allow_push:
            return PolicyDecision.deny("push is denied by default")
        if lowered.startswith("git push") and not self.allow_push:
            return PolicyDecision.deny("push is denied by default")
        if any(token in f" {lowered} " for token in denied_tokens):
            return PolicyDecision.deny("command class is denied by default")
        return PolicyDecision.allow("command allowed")


def _required_string(payload: dict[str, Any], key: str, context: str = "request") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _required_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must contain objects")
    return value
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_request_defaults_to_eight_hour_runtime .\tests\test_autonomous_session.py::test_autonomous_policy_denies_push_deploy_install_and_destructive_commands -v
```

Expected: both tests pass.

## Task 2: Checkpoint Store and Session Resume

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write failing checkpoint and resume tests**

Append:

```python
from bioscaffold.autonomy import AutonomousSessionRecord, AutonomousSessionStatus, SessionCheckpointStore


def test_checkpoint_store_writes_session_generation_and_task_logs(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    store = SessionCheckpointStore(workspace, "session_000001")
    record = AutonomousSessionRecord(
        session_id="session_000001",
        workspace_path=str(workspace),
        organism_id="organism_000001",
        product_name="Authentication Module",
        status=AutonomousSessionStatus.RUNNING,
        max_runtime_seconds=28800,
        generation_index=1,
        checkpoint_dir=str(store.session_dir),
    )

    store.write_checkpoint(record)

    assert (store.session_dir / "session.json").exists()
    assert (store.session_dir / "generation_000001.json").exists()
    assert (store.session_dir / "task_log.jsonl").exists()
    assert json.loads((store.session_dir / "session.json").read_text())["status"] == "running"


def test_checkpoint_store_resumes_session_record(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    store = SessionCheckpointStore(workspace, "session_000001")
    record = AutonomousSessionRecord(
        session_id="session_000001",
        workspace_path=str(workspace),
        organism_id="organism_000001",
        product_name="Authentication Module",
        status=AutonomousSessionStatus.COMPLETED,
        max_runtime_seconds=28800,
        generation_index=1,
        checkpoint_dir=str(store.session_dir),
    )
    store.write_checkpoint(record)

    resumed = SessionCheckpointStore.load(store.session_dir / "session.json")

    assert resumed.session_id == "session_000001"
    assert resumed.status is AutonomousSessionStatus.COMPLETED
    assert resumed.generation_index == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_checkpoint_store_writes_session_generation_and_task_logs .\tests\test_autonomous_session.py::test_checkpoint_store_resumes_session_record -v
```

Expected: import error for `SessionCheckpointStore`.

- [ ] **Step 3: Implement checkpoint store**

Add to `bioscaffold/autonomy.py`:

```python
class SessionCheckpointStore:
    def __init__(self, workspace_path: Path, session_id: str) -> None:
        self.workspace_path = workspace_path.resolve()
        self.session_id = session_id
        self.session_dir = self.workspace_path / ".bioclaw" / "sessions" / session_id

    def write_checkpoint(self, record: AutonomousSessionRecord) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        payload = record.to_payload()
        (self.session_dir / "session.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        generation_path = self.session_dir / f"generation_{record.generation_index:06d}.json"
        generation_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with (self.session_dir / "task_log.jsonl").open("w", encoding="utf-8") as handle:
            for task in record.task_records:
                handle.write(json.dumps(task.to_payload(), sort_keys=True) + "\n")
        with (self.session_dir / "command_log.jsonl").open("w", encoding="utf-8") as handle:
            for command in record.command_records:
                handle.write(json.dumps(command.to_payload(), sort_keys=True) + "\n")

    @classmethod
    def load(cls, session_path: Path) -> AutonomousSessionRecord:
        payload = json.loads(session_path.read_text(encoding="utf-8-sig"))
        return AutonomousSessionRecord(
            session_id=payload["session_id"],
            workspace_path=payload["workspace_path"],
            organism_id=payload["organism_id"],
            product_name=payload["product_name"],
            status=AutonomousSessionStatus(payload["status"]),
            max_runtime_seconds=int(payload["max_runtime_seconds"]),
            generation_index=int(payload["generation_index"]),
            checkpoint_dir=payload["checkpoint_dir"],
            task_records=tuple(
                AutonomousTaskRecord(
                    task_id=item["task_id"],
                    operation=AutonomousOperation(item["operation"]),
                    state=item["state"],
                    reason=item["reason"],
                    path=item.get("path", ""),
                    command=item.get("command", ""),
                    outputs=tuple(item.get("outputs", ())),
                )
                for item in payload.get("task_records", ())
            ),
            command_records=tuple(
                CommandRecord(
                    command=item["command"],
                    exit_code=int(item["exit_code"]),
                    stdout=item.get("stdout", ""),
                    stderr=item.get("stderr", ""),
                )
                for item in payload.get("command_records", ())
            ),
            commit_refs=tuple(payload.get("commit_refs", ())),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_checkpoint_store_writes_session_generation_and_task_logs .\tests\test_autonomous_session.py::test_checkpoint_store_resumes_session_record -v
```

Expected: both tests pass.

## Task 3: Local Executor, Verification Gate, and Commit Gate

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write failing local execution tests**

Append:

```python
import subprocess

from bioscaffold.autonomy import AutonomousSessionController


def init_git_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "bioclaw@example.local"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "BioClaw"], cwd=path, check=True)


def test_autonomous_session_writes_file_verifies_and_commits_generation(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_000001",
            "product_name": "Authentication Module",
            "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
            "project_tasks": [
                {
                    "task_id": "task.write.readme",
                    "operation": "write_file",
                    "path": "README.md",
                    "content": "# Authentication Module\n",
                }
            ],
            "verification_commands": ["python -c \"from pathlib import Path; assert Path('README.md').exists()\""],
        }
    )

    record = AutonomousSessionController().run(request)
    log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=workspace, check=True, capture_output=True, text=True)

    assert record.status is AutonomousSessionStatus.COMPLETED
    assert record.commit_refs
    assert "BioClaw generation 000001" in log.stdout
    assert (workspace / ".bioclaw" / "sessions" / "session_000001" / "session.json").exists()


def test_autonomous_session_blocks_commit_when_verification_fails(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_000001",
            "product_name": "Authentication Module",
            "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
            "project_tasks": [
                {
                    "task_id": "task.write.readme",
                    "operation": "write_file",
                    "path": "README.md",
                    "content": "# Authentication Module\n",
                }
            ],
            "verification_commands": ["python -c \"raise SystemExit(3)\""],
        }
    )

    record = AutonomousSessionController().run(request)
    log = subprocess.run(["git", "log", "--oneline"], cwd=workspace, capture_output=True, text=True)

    assert record.status is AutonomousSessionStatus.BLOCKED
    assert record.commit_refs == ()
    assert log.stdout == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_session_writes_file_verifies_and_commits_generation .\tests\test_autonomous_session.py::test_autonomous_session_blocks_commit_when_verification_fails -v
```

Expected: import error for `AutonomousSessionController`.

- [ ] **Step 3: Implement executor and controller**

Add to `bioscaffold/autonomy.py`:

```python
class LocalAutonomousExecutor:
    def execute(self, request: AutonomousSessionRequest, item: AutonomousWorkItem) -> tuple[AutonomousTaskRecord, tuple[CommandRecord, ...]]:
        if item.operation is AutonomousOperation.WRITE_FILE:
            target = (request.workspace_path / item.path).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.content, encoding="utf-8")
            return (
                AutonomousTaskRecord(
                    task_id=item.task_id,
                    operation=item.operation,
                    state="complete",
                    reason="file written",
                    path=item.path,
                    outputs=(item.path,),
                ),
                (),
            )
        if item.operation is AutonomousOperation.RUN_COMMAND:
            command_record = _run_shell(item.command, request.workspace_path)
            state = "complete" if command_record.exit_code == 0 else "failed"
            return (
                AutonomousTaskRecord(
                    task_id=item.task_id,
                    operation=item.operation,
                    state=state,
                    reason="command completed" if state == "complete" else "command failed",
                    command=item.command,
                ),
                (command_record,),
            )
        return (
            AutonomousTaskRecord(
                task_id=item.task_id,
                operation=item.operation,
                state="complete",
                reason="recorded",
            ),
            (),
        )


class AutonomousSessionController:
    def __init__(self, *, executor: LocalAutonomousExecutor | None = None) -> None:
        self.executor = executor or LocalAutonomousExecutor()

    def run(self, request: AutonomousSessionRequest) -> AutonomousSessionRecord:
        started = time.monotonic()
        store = SessionCheckpointStore(request.workspace_path, request.session_id)
        policy = AutonomousPolicy.default(workspace_path=request.workspace_path, allow_push=request.allow_push)
        task_records: list[AutonomousTaskRecord] = []
        command_records: list[CommandRecord] = []
        status = AutonomousSessionStatus.RUNNING

        for item in request.project_tasks:
            if time.monotonic() - started >= request.max_runtime_seconds:
                status = AutonomousSessionStatus.TIMEOUT
                break
            decision = policy.authorize(item)
            if not decision.allowed:
                task_records.append(
                    AutonomousTaskRecord(
                        task_id=item.task_id,
                        operation=item.operation,
                        state="policy_denied",
                        reason=decision.reason,
                        path=item.path,
                        command=item.command,
                    )
                )
                status = AutonomousSessionStatus.POLICY_DENIED
                break
            task_record, commands = self.executor.execute(request, item)
            task_records.append(task_record)
            command_records.extend(commands)
            if task_record.state != "complete":
                status = AutonomousSessionStatus.FAILED
                break

        if status is AutonomousSessionStatus.RUNNING:
            verification_records = [_run_shell(command, request.workspace_path) for command in request.verification_commands]
            command_records.extend(verification_records)
            if any(record.exit_code != 0 for record in verification_records):
                status = AutonomousSessionStatus.BLOCKED
            else:
                status = AutonomousSessionStatus.COMPLETED

        commit_refs: tuple[str, ...] = ()
        if status is AutonomousSessionStatus.COMPLETED and request.allow_local_commits:
            commit_refs = self._commit_if_needed(request)

        record = AutonomousSessionRecord(
            session_id=request.session_id,
            workspace_path=str(request.workspace_path),
            organism_id=request.organism_id,
            product_name=request.product_name,
            status=status,
            max_runtime_seconds=request.max_runtime_seconds,
            generation_index=1,
            task_records=tuple(task_records),
            command_records=tuple(command_records),
            commit_refs=commit_refs,
            checkpoint_dir=str(store.session_dir),
        )
        store.write_checkpoint(record)
        return record

    def _commit_if_needed(self, request: AutonomousSessionRequest) -> tuple[str, ...]:
        diff = subprocess.run(["git", "status", "--porcelain"], cwd=request.workspace_path, capture_output=True, text=True, check=False)
        if not diff.stdout.strip():
            return ()
        subprocess.run(["git", "add", "-A"], cwd=request.workspace_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"BioClaw generation 000001: {request.product_name}"],
            cwd=request.workspace_path,
            check=True,
            capture_output=True,
            text=True,
        )
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=request.workspace_path, check=True, capture_output=True, text=True)
        return (rev.stdout.strip(),)


def _run_shell(command: str, cwd: Path) -> CommandRecord:
    completed = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True, check=False)
    return CommandRecord(
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_session_writes_file_verifies_and_commits_generation .\tests\test_autonomous_session.py::test_autonomous_session_blocks_commit_when_verification_fails -v
```

Expected: both tests pass.

## Task 4: Timeout and Resume Behavior

**Files:**
- Modify: `bioscaffold/autonomy.py`
- Test: `tests/test_autonomous_session.py`

- [ ] **Step 1: Write failing timeout and resume tests**

Append:

```python
def test_autonomous_session_records_timeout_before_work(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_000001",
            "product_name": "Authentication Module",
            "max_runtime_seconds": 0,
            "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
            "project_tasks": [
                {
                    "task_id": "task.write.readme",
                    "operation": "write_file",
                    "path": "README.md",
                    "content": "# Authentication Module\n",
                }
            ],
            "verification_commands": [],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.TIMEOUT
    assert (workspace / ".bioclaw" / "sessions" / "session_000001" / "session.json").exists()


def test_autonomous_session_resume_returns_saved_record(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_000001",
            "product_name": "Authentication Module",
            "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
            "project_tasks": [
                {
                    "task_id": "task.write.readme",
                    "operation": "write_file",
                    "path": "README.md",
                    "content": "# Authentication Module\n",
                }
            ],
            "verification_commands": [],
        }
    )
    original = AutonomousSessionController().run(request)

    resumed = AutonomousSessionController().resume(Path(original.checkpoint_dir) / "session.json")

    assert resumed.session_id == original.session_id
    assert resumed.status is AutonomousSessionStatus.COMPLETED
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_session_records_timeout_before_work .\tests\test_autonomous_session.py::test_autonomous_session_resume_returns_saved_record -v
```

Expected: timeout behavior or `resume` missing fails.

- [ ] **Step 3: Implement resume and strict timeout check**

Modify `AutonomousSessionController.run()` timeout check to evaluate before executing each item:

```python
if request.max_runtime_seconds <= 0 or time.monotonic() - started >= request.max_runtime_seconds:
    status = AutonomousSessionStatus.TIMEOUT
    break
```

Add:

```python
    def resume(self, session_path: Path) -> AutonomousSessionRecord:
        return SessionCheckpointStore.load(session_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py::test_autonomous_session_records_timeout_before_work .\tests\test_autonomous_session.py::test_autonomous_session_resume_returns_saved_record -v
```

Expected: both tests pass.

## Task 5: CLI Commands

**Files:**
- Modify: `bioscaffold/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Append to `tests/test_cli.py`:

```python
import subprocess


def test_run_session_command_writes_session_json(tmp_path, capsys):
    workspace = tmp_path / "project"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "bioclaw@example.local"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "BioClaw"], cwd=workspace, check=True)
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "session_id": "session_000001",
                "workspace_path": str(workspace),
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
                "project_tasks": [
                    {
                        "task_id": "task.write.readme",
                        "operation": "write_file",
                        "path": "README.md",
                        "content": "# Authentication Module\n",
                    }
                ],
                "verification_commands": [],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["run-session", str(request_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"
    assert payload["session_id"] == "session_000001"


def test_session_status_command_reads_session_json(tmp_path, capsys):
    workspace = tmp_path / "project"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "bioclaw@example.local"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "BioClaw"], cwd=workspace, check=True)
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "session_id": "session_000001",
                "workspace_path": str(workspace),
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [{"requirement_id": "readme", "text": "Create readme."}],
                "project_tasks": [
                    {
                        "task_id": "task.write.readme",
                        "operation": "write_file",
                        "path": "README.md",
                        "content": "# Authentication Module\n",
                    }
                ],
                "verification_commands": [],
            }
        ),
        encoding="utf-8",
    )
    main(["run-session", str(request_path)])
    capsys.readouterr()
    session_path = workspace / ".bioclaw" / "sessions" / "session_000001" / "session.json"

    exit_code = main(["session-status", str(session_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest .\tests\test_cli.py::test_run_session_command_writes_session_json .\tests\test_cli.py::test_session_status_command_reads_session_json -v
```

Expected: argparse rejects `run-session`.

- [ ] **Step 3: Wire CLI commands**

Modify `bioscaffold/cli.py` imports:

```python
from bioscaffold.autonomy import AutonomousSessionController, AutonomousSessionRequest, SessionCheckpointStore
```

Add subparsers in `_build_parser()`:

```python
    run_session = subparsers.add_parser(
        "run-session",
        help="Run a local-only autonomous project session.",
    )
    run_session.add_argument("request", type=Path)
    run_session.add_argument("--pretty", action="store_true")

    resume_session = subparsers.add_parser(
        "resume-session",
        help="Resume by reading an autonomous session checkpoint.",
    )
    resume_session.add_argument("session", type=Path)
    resume_session.add_argument("--pretty", action="store_true")

    session_status = subparsers.add_parser(
        "session-status",
        help="Print autonomous session checkpoint status JSON.",
    )
    session_status.add_argument("session", type=Path)
    session_status.add_argument("--pretty", action="store_true")
```

Modify `main()`:

```python
    if args.command == "run-session":
        return _run_session(args)
    if args.command == "resume-session":
        return _resume_session(args)
    if args.command == "session-status":
        return _session_status(args)
```

Add helpers:

```python
def _run_session(args: argparse.Namespace) -> int:
    try:
        payload = json.loads(args.request.read_text(encoding="utf-8-sig"))
        request = AutonomousSessionRequest.from_payload(payload)
        record = AutonomousSessionController().run(request)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(record.to_payload(), pretty=args.pretty)
    return 0


def _resume_session(args: argparse.Namespace) -> int:
    try:
        record = AutonomousSessionController().resume(args.session)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(record.to_payload(), pretty=args.pretty)
    return 0


def _session_status(args: argparse.Namespace) -> int:
    return _resume_session(args)


def _print_json(payload: dict[str, Any], *, pretty: bool) -> None:
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest .\tests\test_cli.py::test_run_session_command_writes_session_json .\tests\test_cli.py::test_session_status_command_reads_session_json -v
```

Expected: both tests pass.

## Task 6: Public Exports and Documentation

**Files:**
- Modify: `bioscaffold/__init__.py`
- Modify: `tests/test_component_cards.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing public import expectation**

In `tests/test_component_cards.py::test_package_imports`, add these names to the expected `bioscaffold.__all__` list in alphabetical/location order near other autonomy exports:

```python
        "AutonomousOperation",
        "AutonomousPolicy",
        "AutonomousSessionController",
        "AutonomousSessionRecord",
        "AutonomousSessionRequest",
        "AutonomousSessionStatus",
        "AutonomousTaskRecord",
        "AutonomousWorkItem",
        "CommandRecord",
        "LocalAutonomousExecutor",
        "SessionCheckpointStore",
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest .\tests\test_component_cards.py::test_package_imports -v
```

Expected: assertion failure because exports are missing.

- [ ] **Step 3: Export autonomous session types**

Add to `bioscaffold/__init__.py`:

```python
from bioscaffold.autonomy import (
    AutonomousOperation,
    AutonomousPolicy,
    AutonomousSessionController,
    AutonomousSessionRecord,
    AutonomousSessionRequest,
    AutonomousSessionStatus,
    AutonomousTaskRecord,
    AutonomousWorkItem,
    CommandRecord,
    LocalAutonomousExecutor,
    SessionCheckpointStore,
)
```

Add matching strings to `__all__`.

- [ ] **Step 4: Document CLI usage**

Add to `README.md` after the existing OpenClaw entrypoint section:

```markdown
### Autonomous Session Mode

For local-only autonomous project work:

```powershell
python -m bioscaffold run-session .\autonomous-request.json --pretty
python -m bioscaffold session-status .\.bioclaw\sessions\<session_id>\session.json --pretty
python -m bioscaffold resume-session .\.bioclaw\sessions\<session_id>\session.json --pretty
```

The default runtime budget is eight hours. The first autonomous mode allows local file edits, local verification commands, checkpoint writes, and local commits. It denies push, deploy, publish, install, destructive commands, secret reads, and commands outside the workspace by default.
```

- [ ] **Step 5: Run public import test**

Run:

```powershell
python -m pytest .\tests\test_component_cards.py::test_package_imports -v
```

Expected: pass.

## Task 7: Full Verification and Commit

**Files:**
- All changed files from Tasks 1-6

- [ ] **Step 1: Run focused autonomous tests**

Run:

```powershell
python -m pytest .\tests\test_autonomous_session.py .\tests\test_cli.py .\tests\test_component_cards.py::test_package_imports -v
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected: exit code `0`. Windows CRLF warnings are acceptable if no whitespace errors are reported.

- [ ] **Step 4: Run a real CLI smoke**

Use a temp git repo and request file:

```powershell
$root = Join-Path $env:TEMP "bioclaw-autonomy-smoke"
if (Test-Path $root) { Remove-Item -LiteralPath $root -Recurse -Force }
New-Item -ItemType Directory -Path $root | Out-Null
git -C $root init
git -C $root config user.email "bioclaw@example.local"
git -C $root config user.name "BioClaw"
$request = Join-Path $root "request.json"
@"
{
  "session_id": "session_000001",
  "workspace_path": "$($root -replace '\\','/')",
  "organism_id": "organism_000001",
  "product_name": "Authentication Module",
  "requirements": [
    { "requirement_id": "readme", "text": "Create readme." }
  ],
  "project_tasks": [
    {
      "task_id": "task.write.readme",
      "operation": "write_file",
      "path": "README.md",
      "content": "# Authentication Module\n"
    }
  ],
  "verification_commands": [
    "python -c \"from pathlib import Path; assert Path('README.md').exists()\""
  ]
}
"@ | Set-Content -Path $request -Encoding UTF8
python -m bioscaffold run-session $request --pretty
git -C $root log --oneline -1
```

Expected:

- CLI JSON reports `status` as `completed`;
- `.bioclaw/sessions/session_000001/session.json` exists;
- git log contains `BioClaw generation 000001`.

- [ ] **Step 5: Commit implementation**

Run:

```powershell
git add .\bioscaffold\autonomy.py .\bioscaffold\cli.py .\bioscaffold\__init__.py .\tests\test_autonomous_session.py .\tests\test_cli.py .\tests\test_component_cards.py .\README.md
git commit -m "Add autonomous local work sessions"
```

Expected: commit succeeds.

- [ ] **Step 6: Push if user has asked to publish**

If Jake says to push, run:

```powershell
git push origin main
```

Expected: branch updates on origin.

## Self-Review

- Spec coverage: request validation, eight-hour default, policy denial, checkpointing, resume, verification gate, local commit gate, timeout, and CLI commands are each mapped to a task.
- Placeholder scan: no implementation task relies on unspecified behavior or missing function names.
- Type consistency: all planned types use `Autonomous*` names and the CLI imports match the planned module.
