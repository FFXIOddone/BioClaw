from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
import subprocess
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
        return cls(
            task_id=_required_string(payload, "task_id", "project_tasks[]"),
            operation=AutonomousOperation(_required_string(payload, "operation", "project_tasks[]")),
            path=_optional_string(payload, "path", "project_tasks[]"),
            content=_optional_string(payload, "content", "project_tasks[]"),
            command=_optional_string(payload, "command", "project_tasks[]"),
            expected_output=_optional_string(payload, "expected_output", "project_tasks[]"),
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
                markers=tuple(str(marker) for marker in item.get("markers", ())),
            )
            for item in _required_list(payload, "requirements")
        )
        project_tasks = tuple(
            AutonomousWorkItem.from_payload(item)
            for item in _required_list(payload, "project_tasks")
        )
        if not requirements:
            raise ValueError("requirements must contain at least one item")
        if not project_tasks:
            raise ValueError("project_tasks must contain at least one item")

        return cls(
            session_id=_required_string(payload, "session_id"),
            workspace_path=Path(_required_string(payload, "workspace_path")).resolve(),
            organism_id=_required_string(payload, "organism_id"),
            product_name=_required_string(payload, "product_name"),
            requirements=requirements,
            project_tasks=project_tasks,
            verification_commands=_optional_string_sequence(payload, "verification_commands"),
            max_runtime_seconds=int(payload.get("max_runtime_seconds", 28800)),
            generation_limit=int(payload.get("generation_limit", 24)),
            turn_limit=int(payload.get("turn_limit", 96)),
            allow_local_edits=_optional_bool(payload, "allow_local_edits", True),
            allow_local_commits=_optional_bool(payload, "allow_local_commits", True),
            allow_push=_optional_bool(payload, "allow_push", False),
            allow_dirty_start=_optional_bool(payload, "allow_dirty_start", False),
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


class SessionCheckpointStore:
    def __init__(self, workspace_path: Path, session_id: str) -> None:
        self.workspace_path = workspace_path.resolve()
        _validate_session_id(session_id)
        self.session_id = session_id
        self.sessions_root = (self.workspace_path / ".bioclaw" / "sessions").resolve()
        self.session_dir = (self.sessions_root / session_id).resolve()
        try:
            self.session_dir.relative_to(self.sessions_root)
        except ValueError as exc:
            raise ValueError("session_id must resolve under workspace session storage") from exc

    def write_checkpoint(self, record: AutonomousSessionRecord) -> None:
        if record.session_id != self.session_id:
            raise ValueError("record.session_id does not match checkpoint store session_id")
        if Path(record.workspace_path).resolve() != self.workspace_path:
            raise ValueError("record.workspace_path does not match checkpoint store workspace_path")
        if record.generation_index < 0:
            raise ValueError("record.generation_index must be non-negative")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        payload = record.to_payload()
        session_content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        (self.session_dir / "session.json").write_text(session_content, encoding="utf-8")
        (self.session_dir / f"generation_{record.generation_index:06d}.json").write_text(
            session_content,
            encoding="utf-8",
        )
        # Logs are rewritten from the record's complete in-memory history.
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


class LocalAutonomousExecutor:
    def __init__(
        self,
        *,
        workspace_path: Path,
        policy: AutonomousPolicy,
        allow_local_edits: bool = True,
    ) -> None:
        self.workspace_path = workspace_path.resolve()
        self.policy = policy
        self.allow_local_edits = allow_local_edits

    def execute(self, item: AutonomousWorkItem) -> tuple[AutonomousTaskRecord, tuple[CommandRecord, ...]]:
        decision = self.policy.authorize(item)
        if not decision.allowed:
            return (
                AutonomousTaskRecord(
                    task_id=item.task_id,
                    operation=item.operation,
                    state=AutonomousSessionStatus.POLICY_DENIED.value,
                    reason=decision.reason,
                    path=item.path,
                    command=item.command,
                ),
                (),
            )

        if item.operation is AutonomousOperation.WRITE_FILE:
            return self._write_file(item), ()
        if item.operation is AutonomousOperation.RUN_COMMAND:
            command = _run_shell(item.command, cwd=self.workspace_path)
            state = "completed" if command.exit_code == 0 else "failed"
            reason = "command completed" if command.exit_code == 0 else f"command failed with exit code {command.exit_code}"
            return (
                AutonomousTaskRecord(
                    task_id=item.task_id,
                    operation=item.operation,
                    state=state,
                    reason=reason,
                    command=item.command,
                    outputs=(command.stdout, command.stderr),
                ),
                (command,),
            )

        return (
            AutonomousTaskRecord(
                task_id=item.task_id,
                operation=item.operation,
                state="completed",
                reason="operation recorded",
                path=item.path,
                command=item.command,
            ),
            (),
        )

    def _write_file(self, item: AutonomousWorkItem) -> AutonomousTaskRecord:
        if not self.allow_local_edits:
            return AutonomousTaskRecord(
                task_id=item.task_id,
                operation=item.operation,
                state="blocked",
                reason="local edits are disabled",
                path=item.path,
            )

        target = (self.workspace_path / item.path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item.content, encoding="utf-8")
        return AutonomousTaskRecord(
            task_id=item.task_id,
            operation=item.operation,
            state="completed",
            reason=f"wrote {item.path}",
            path=item.path,
            outputs=(item.path,),
        )


class AutonomousSessionController:
    def run(self, request: AutonomousSessionRequest) -> AutonomousSessionRecord:
        workspace_path = request.workspace_path.resolve()
        generation_index = 1
        store = SessionCheckpointStore(workspace_path, request.session_id)
        policy = AutonomousPolicy.default(workspace_path=workspace_path, allow_push=request.allow_push)
        executor = LocalAutonomousExecutor(
            workspace_path=workspace_path,
            policy=policy,
            allow_local_edits=request.allow_local_edits,
        )
        task_records: list[AutonomousTaskRecord] = []
        command_records: list[CommandRecord] = []
        commit_refs: list[str] = []
        status = AutonomousSessionStatus.COMPLETED

        for item in request.project_tasks:
            task_record, item_command_records = executor.execute(item)
            task_records.append(task_record)
            command_records.extend(item_command_records)
            if task_record.state == AutonomousSessionStatus.POLICY_DENIED.value:
                status = AutonomousSessionStatus.POLICY_DENIED
                break
            if task_record.state != "completed":
                status = AutonomousSessionStatus.BLOCKED
                break

        if status is AutonomousSessionStatus.COMPLETED:
            status = self._run_verification(request, policy, command_records)

        if status is AutonomousSessionStatus.COMPLETED and request.allow_local_commits:
            status = self._commit_if_changed(
                workspace_path,
                request.session_id,
                generation_index,
                command_records,
                commit_refs,
            )

        record = AutonomousSessionRecord(
            session_id=request.session_id,
            workspace_path=str(workspace_path),
            organism_id=request.organism_id,
            product_name=request.product_name,
            status=status,
            max_runtime_seconds=request.max_runtime_seconds,
            generation_index=generation_index,
            checkpoint_dir=str(store.session_dir),
            task_records=tuple(task_records),
            command_records=tuple(command_records),
            commit_refs=tuple(commit_refs),
        )
        store.write_checkpoint(record)
        return record

    def _run_verification(
        self,
        request: AutonomousSessionRequest,
        policy: AutonomousPolicy,
        command_records: list[CommandRecord],
    ) -> AutonomousSessionStatus:
        for index, command in enumerate(request.verification_commands, start=1):
            decision = policy.authorize(
                AutonomousWorkItem(
                    task_id=f"verification.{index}",
                    operation=AutonomousOperation.RUN_COMMAND,
                    command=command,
                )
            )
            if not decision.allowed:
                command_records.append(CommandRecord(command=command, exit_code=1, stdout="", stderr=decision.reason))
                return AutonomousSessionStatus.POLICY_DENIED

            record = _run_shell(command, cwd=request.workspace_path)
            command_records.append(record)
            if record.exit_code != 0:
                return AutonomousSessionStatus.BLOCKED

        return AutonomousSessionStatus.COMPLETED

    def _commit_if_changed(
        self,
        workspace_path: Path,
        session_id: str,
        generation_index: int,
        command_records: list[CommandRecord],
        commit_refs: list[str],
    ) -> AutonomousSessionStatus:
        status_record = _run_shell("git status --porcelain", cwd=workspace_path)
        command_records.append(status_record)
        if status_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED
        if not status_record.stdout.strip():
            return AutonomousSessionStatus.COMPLETED

        add_record = _run_shell("git add -A", cwd=workspace_path)
        command_records.append(add_record)
        if add_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED

        commit_record = _run_shell(
            f'git commit -m "Autonomous session {session_id} generation {generation_index}"',
            cwd=workspace_path,
        )
        command_records.append(commit_record)
        if commit_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED

        rev_parse_record = _run_shell("git rev-parse HEAD", cwd=workspace_path)
        command_records.append(rev_parse_record)
        if rev_parse_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED

        commit_refs.append(rev_parse_record.stdout.strip())
        return AutonomousSessionStatus.COMPLETED


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")
    session_path = Path(session_id)
    if session_path.is_absolute() or session_path.name != session_id or session_id in {".", ".."}:
        raise ValueError("session_id must be one safe path segment")


class AutonomousPolicy:
    def __init__(self, *, workspace_path: Path, allow_push: bool = False) -> None:
        self.workspace_path = workspace_path.resolve()
        if not isinstance(allow_push, bool):
            raise ValueError("allow_push must be a boolean")
        self.allow_push = allow_push

    @classmethod
    def default(cls, *, workspace_path: Path, allow_push: bool = False) -> "AutonomousPolicy":
        return cls(workspace_path=workspace_path, allow_push=allow_push)

    def authorize(self, item: AutonomousWorkItem) -> PolicyDecision:
        if item.operation in (
            AutonomousOperation.INSPECT_FILE,
            AutonomousOperation.WRITE_FILE,
            AutonomousOperation.RECORD,
        ):
            return self._authorize_path(item.path)
        if item.operation is AutonomousOperation.RUN_COMMAND:
            return self._authorize_command(item.command)
        if item.operation is AutonomousOperation.GIT_COMMIT:
            return PolicyDecision.deny("git commit is denied until commit gate authorization")
        return PolicyDecision.allow("operation allowed")

    def _authorize_path(self, relative_path: str) -> PolicyDecision:
        if not relative_path:
            return PolicyDecision.deny("path is required")
        target = (self.workspace_path / relative_path).resolve()
        try:
            target.relative_to(self.workspace_path)
        except ValueError:
            return PolicyDecision.deny("path escapes workspace")
        return PolicyDecision.allow("path is inside workspace")

    def _authorize_command(self, command: str) -> PolicyDecision:
        if not command.strip():
            return PolicyDecision.deny("command is required")
        tokens = _command_tokens(command)
        if _is_git_commit(tokens):
            return PolicyDecision.deny("git commit is only allowed through the internal commit gate")
        if _is_git_push(tokens) and not self.allow_push:
            return PolicyDecision.deny("push is denied by default")
        denied_commands = {"deploy", "publish", "install", "remove-item", "rm", "rmdir", "del", "erase", "rd"}
        if any(token in denied_commands for token in tokens):
            return PolicyDecision.deny("command class is denied by default")
        return PolicyDecision.allow("command allowed")


def _required_string(payload: dict[str, Any], key: str, context: str = "request") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _optional_string(payload: dict[str, Any], key: str, context: str) -> str:
    if key not in payload:
        return ""
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{context}.{key} must be a string")
    return value


def _optional_string_sequence(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    if key not in payload:
        return ()
    value = payload[key]
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{key} must be a list or tuple of strings")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{key} must contain only strings")
    return tuple(value)


def _optional_bool(payload: dict[str, Any], key: str, default: bool) -> bool:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _required_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must contain objects")
    return value


def _command_tokens(command: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s+", " ", command.strip().lower())
    return tuple(token.strip("\"'`") for token in re.split(r"[;&| ]+", normalized) if token.strip("\"'`"))


def _is_git_push(tokens: tuple[str, ...]) -> bool:
    return _has_git_subcommand(tokens, "push")


def _is_git_commit(tokens: tuple[str, ...]) -> bool:
    return _has_git_subcommand(tokens, "commit")


def _has_git_subcommand(tokens: tuple[str, ...], subcommand: str) -> bool:
    return any(
        token in {"git", "git.exe"} and index + 1 < len(tokens) and tokens[index + 1] == subcommand
        for index, token in enumerate(tokens)
    )


def _run_shell(command: str, *, cwd: Path) -> CommandRecord:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        return CommandRecord(command=command, exit_code=127, stdout="", stderr=str(exc))
    return CommandRecord(
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
