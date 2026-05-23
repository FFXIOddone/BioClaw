from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
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
    return tuple(token for token in re.split(r"[;&| ]+", normalized) if token)


def _is_git_push(tokens: tuple[str, ...]) -> bool:
    return len(tokens) >= 2 and tokens[0] in {"git", "git.exe"} and tokens[1] == "push"
