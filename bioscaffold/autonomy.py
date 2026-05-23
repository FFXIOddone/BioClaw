from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Callable

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


class SeedGenerationStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    POLICY_DENIED = "policy_denied"
    TIMEOUT = "timeout"
    GENERATION_LIMIT_REACHED = "generation_limit_reached"


@dataclass(frozen=True)
class AutonomousWorkItem:
    task_id: str
    operation: AutonomousOperation
    path: str = ""
    content: str = ""
    command: str = ""
    expected_output: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "operation": self.operation.value,
            "path": self.path,
            "content": self.content,
            "command": self.command,
            "expected_output": self.expected_output,
        }

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
class SeedAutonomousRequest:
    session_id: str
    workspace_path: Path
    organism_id: str
    product_name: str
    seed_goal: str
    verification_commands: tuple[str, ...]
    max_runtime_seconds: int = 28800
    generation_limit: int = 4
    allow_local_edits: bool = True
    allow_local_commits: bool = True
    allow_push: bool = False
    allow_dirty_start: bool = False
    run_until_runtime_exhausted: bool = False
    turn_delay_seconds: int = 0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SeedAutonomousRequest":
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

        turn_delay_seconds = _optional_int(payload, "turn_delay_seconds", 0)
        if turn_delay_seconds < 0:
            raise ValueError("turn_delay_seconds must be greater than or equal to zero")

        return cls(
            session_id=_required_string(payload, "session_id"),
            workspace_path=Path(_required_string(payload, "workspace_path")).resolve(),
            organism_id=_required_string(payload, "organism_id"),
            product_name=_required_string(payload, "product_name"),
            seed_goal=_required_string(payload, "seed_goal"),
            verification_commands=_optional_string_sequence(payload, "verification_commands"),
            max_runtime_seconds=_optional_int(payload, "max_runtime_seconds", 28800),
            generation_limit=_optional_int(payload, "generation_limit", 4),
            allow_local_edits=_optional_bool(payload, "allow_local_edits", True),
            allow_local_commits=_optional_bool(payload, "allow_local_commits", True),
            allow_push=_optional_bool(payload, "allow_push", False),
            allow_dirty_start=_optional_bool(payload, "allow_dirty_start", False),
            run_until_runtime_exhausted=_optional_bool(payload, "run_until_runtime_exhausted", False),
            turn_delay_seconds=turn_delay_seconds,
        )


@dataclass(frozen=True)
class SeedGenerationPlan:
    generation_index: int
    project_tasks: tuple[AutonomousWorkItem, ...]
    verification_commands: tuple[str, ...]
    is_terminal: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "generation_index": self.generation_index,
            "project_tasks": [task.to_payload() for task in self.project_tasks],
            "verification_commands": list(self.verification_commands),
            "is_terminal": self.is_terminal,
        }


@dataclass(frozen=True)
class SeedGenerationRecord:
    generation_index: int
    project_tasks: tuple[AutonomousWorkItem, ...]
    verification_commands: tuple[str, ...]
    status: SeedGenerationStatus = SeedGenerationStatus.PLANNED
    terminal: bool = False
    reason: str = ""
    inner_checkpoint_path: str = ""
    inner_status: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "generation_index": self.generation_index,
            "project_tasks": [task.to_payload() for task in self.project_tasks],
            "verification_commands": list(self.verification_commands),
            "status": self.status.value,
            "terminal": self.terminal,
            "reason": self.reason,
            "inner_checkpoint_path": self.inner_checkpoint_path,
            "inner_status": self.inner_status,
        }


class SeedAutonomousController:
    def __init__(
        self,
        *,
        planner: SeedMicrotaskPlanner | None = None,
        session_controller: AutonomousSessionController | None = None,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.planner = planner or SeedMicrotaskPlanner()
        self.session_controller = session_controller or AutonomousSessionController()
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep

    def run(self, request: SeedAutonomousRequest) -> SeedAutonomousRecord:
        workspace_path = request.workspace_path.resolve()
        seed_session_dir = (workspace_path / ".bioclaw" / "seeds" / request.session_id).resolve()
        generations: list[SeedGenerationRecord] = []
        started_at = self.clock()

        status = SeedGenerationStatus.GENERATION_LIMIT_REACHED if request.generation_limit <= 0 else SeedGenerationStatus.COMPLETED

        for generation_index in range(1, request.generation_limit + 1):
            if request.run_until_runtime_exhausted and self._runtime_exhausted(request, started_at):
                status = SeedGenerationStatus.COMPLETED
                break

            plan = self.planner.plan_generation(request, generation_index=generation_index)

            if plan.is_terminal or not plan.project_tasks:
                generation = SeedGenerationRecord(
                    generation_index=plan.generation_index,
                    project_tasks=plan.project_tasks,
                    verification_commands=plan.verification_commands,
                    status=SeedGenerationStatus.COMPLETED,
                    terminal=True,
                    reason="No remaining work to plan.",
                )
                generations.append(generation)
                status = SeedGenerationStatus.COMPLETED
                break

            inner_request_payload = {
                "session_id": f"{request.session_id}_g{generation_index:06d}",
                "workspace_path": str(workspace_path),
                "organism_id": request.organism_id,
                "product_name": request.product_name,
                "requirements": [
                    {
                        "requirement_id": "seed_goal",
                        "text": request.seed_goal,
                        "artifact_type": "code",
                    },
                ],
                "project_tasks": [task.to_payload() for task in plan.project_tasks],
                "verification_commands": list(plan.verification_commands),
                "max_runtime_seconds": self._remaining_runtime_seconds(request, started_at),
                "allow_local_edits": request.allow_local_edits,
                "allow_local_commits": request.allow_local_commits,
                "allow_push": request.allow_push,
                "allow_dirty_start": request.allow_dirty_start,
            }

            inner_record = self.session_controller.run(
                AutonomousSessionRequest.from_payload(inner_request_payload)
            )
            inner_checkpoint_path = inner_record.checkpoint_dir
            inner_status = inner_record.status
            if inner_status is AutonomousSessionStatus.COMPLETED:
                generation = SeedGenerationRecord(
                    generation_index=plan.generation_index,
                    project_tasks=plan.project_tasks,
                    verification_commands=plan.verification_commands,
                    status=SeedGenerationStatus.COMPLETED,
                    terminal=False,
                    reason="inner session completed.",
                    inner_checkpoint_path=inner_checkpoint_path,
                    inner_status=inner_status.value,
                )
                generations.append(generation)
                if request.run_until_runtime_exhausted:
                    if self._runtime_exhausted(request, started_at):
                        status = SeedGenerationStatus.COMPLETED
                        break
                    if generation_index < request.generation_limit and request.turn_delay_seconds > 0:
                        self.sleep(min(request.turn_delay_seconds, self._remaining_runtime_seconds(request, started_at)))
                        if self._runtime_exhausted(request, started_at):
                            status = SeedGenerationStatus.COMPLETED
                            break
                continue

            mapped_status = self._map_inner_status(inner_status)
            generation = SeedGenerationRecord(
                generation_index=plan.generation_index,
                project_tasks=plan.project_tasks,
                verification_commands=plan.verification_commands,
                status=mapped_status,
                terminal=True,
                reason=f"inner session ended with {inner_status.value}.",
                inner_checkpoint_path=inner_checkpoint_path,
                inner_status=inner_status.value,
            )
            generations.append(generation)
            status = mapped_status
            break

        else:
            if generations:
                status = SeedGenerationStatus.GENERATION_LIMIT_REACHED

        seed_session_dir.mkdir(parents=True, exist_ok=True)
        payload = SeedAutonomousRecord(
            session_id=request.session_id,
            workspace_path=str(workspace_path),
            organism_id=request.organism_id,
            product_name=request.product_name,
            seed_goal=request.seed_goal,
            status=status,
            generation_limit=request.generation_limit,
            max_runtime_seconds=request.max_runtime_seconds,
            run_until_runtime_exhausted=request.run_until_runtime_exhausted,
            turn_delay_seconds=request.turn_delay_seconds,
            generations=tuple(generations),
        ).to_payload()
        (seed_session_dir / "seed-session.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return SeedAutonomousRecord(
            session_id=request.session_id,
            workspace_path=str(workspace_path),
            organism_id=request.organism_id,
            product_name=request.product_name,
            seed_goal=request.seed_goal,
            status=status,
            generation_limit=request.generation_limit,
            max_runtime_seconds=request.max_runtime_seconds,
            run_until_runtime_exhausted=request.run_until_runtime_exhausted,
            turn_delay_seconds=request.turn_delay_seconds,
            generations=tuple(generations),
        )

    def _runtime_exhausted(self, request: SeedAutonomousRequest, started_at: float) -> bool:
        return self.clock() - started_at >= request.max_runtime_seconds

    def _remaining_runtime_seconds(self, request: SeedAutonomousRequest, started_at: float) -> int:
        if not request.run_until_runtime_exhausted:
            return request.max_runtime_seconds
        remaining = request.max_runtime_seconds - (self.clock() - started_at)
        if remaining <= 0:
            return 0
        return max(1, int(remaining))

    @staticmethod
    def _map_inner_status(inner_status: AutonomousSessionStatus) -> SeedGenerationStatus:
        if inner_status is AutonomousSessionStatus.BLOCKED:
            return SeedGenerationStatus.BLOCKED
        if inner_status is AutonomousSessionStatus.POLICY_DENIED:
            return SeedGenerationStatus.POLICY_DENIED
        if inner_status is AutonomousSessionStatus.TIMEOUT:
            return SeedGenerationStatus.TIMEOUT
        if inner_status is AutonomousSessionStatus.FAILED:
            return SeedGenerationStatus.BLOCKED
        return SeedGenerationStatus.BLOCKED


@dataclass(frozen=True)
class SeedAutonomousRecord:
    session_id: str
    workspace_path: str
    organism_id: str
    product_name: str
    seed_goal: str
    status: SeedGenerationStatus
    generation_limit: int
    max_runtime_seconds: int
    run_until_runtime_exhausted: bool = False
    turn_delay_seconds: int = 0
    generations: tuple[SeedGenerationRecord, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "workspace_path": self.workspace_path,
            "organism_id": self.organism_id,
            "product_name": self.product_name,
            "seed_goal": self.seed_goal,
            "status": self.status.value,
            "generation_limit": self.generation_limit,
            "max_runtime_seconds": self.max_runtime_seconds,
            "run_until_runtime_exhausted": self.run_until_runtime_exhausted,
            "turn_delay_seconds": self.turn_delay_seconds,
            "generations": [generation.to_payload() for generation in self.generations],
        }


class SeedMicrotaskPlanner:
    def plan_generation(self, request: SeedAutonomousRequest, generation_index: int) -> SeedGenerationPlan:
        workspace_path = request.workspace_path.resolve()
        baseline_command = _seed_baseline_command(workspace_path / "tests")
        _ = _repo_has_local_fact(workspace_path / "README.md")
        _ = _repo_has_local_fact(workspace_path / "pyproject.toml")

        existing_gitignore = workspace_path / ".gitignore"
        seed_gitignore_entries = _seed_gitignore_entries(workspace_path)
        verification_commands = request.verification_commands or (baseline_command,)
        if _is_gitignore_seed_ready(existing_gitignore, seed_gitignore_entries):
            if request.run_until_runtime_exhausted:
                return SeedGenerationPlan(
                    generation_index=generation_index,
                    project_tasks=(
                        AutonomousWorkItem(
                            task_id=f"seed_generation_{generation_index:06d}.terminal_verification",
                            operation=AutonomousOperation.RUN_COMMAND,
                            command=verification_commands[0],
                        ),
                    ),
                    verification_commands=verification_commands,
                    is_terminal=False,
                )
            return SeedGenerationPlan(
                generation_index=generation_index,
                project_tasks=(),
                verification_commands=(),
                is_terminal=True,
            )

        if existing_gitignore.exists():
            current_gitignore = existing_gitignore.read_text(encoding="utf-8")
            rewritten_gitignore = _append_seed_gitignore_entries(current_gitignore, seed_gitignore_entries)
        else:
            rewritten_gitignore = _append_seed_gitignore_entries("", seed_gitignore_entries)

        tasks = (
            AutonomousWorkItem(
                task_id=f"seed_generation_{generation_index:06d}.gitignore",
                operation=AutonomousOperation.WRITE_FILE,
                path=".gitignore",
                content=rewritten_gitignore,
            ),
            AutonomousWorkItem(
                task_id=f"seed_generation_{generation_index:06d}.baseline",
                operation=AutonomousOperation.RUN_COMMAND,
                command=baseline_command,
            ),
        )

        return SeedGenerationPlan(
            generation_index=generation_index,
            project_tasks=tasks,
            verification_commands=verification_commands,
            is_terminal=False,
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
    def _git_status_without_bioclaw(self, workspace_path: Path) -> CommandRecord:
        return _run_shell("git status --porcelain --untracked-files=all -- . :!.bioclaw", cwd=workspace_path)

    def _check_clean_start(self, workspace_path: Path, command_records: list[CommandRecord]) -> AutonomousSessionStatus:
        status_record = self._git_status_without_bioclaw(workspace_path)
        command_records.append(status_record)
        if status_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED
        if status_record.stdout.strip():
            return AutonomousSessionStatus.BLOCKED
        return AutonomousSessionStatus.COMPLETED

    def run(self, request: AutonomousSessionRequest) -> AutonomousSessionRecord:
        workspace_path = request.workspace_path.resolve()
        generation_index = 1
        started_at = time.monotonic()
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

        if status is AutonomousSessionStatus.COMPLETED and not request.allow_dirty_start:
            status = self._check_clean_start(workspace_path, command_records)

        for item in request.project_tasks:
            if status is not AutonomousSessionStatus.COMPLETED:
                break
            if request.max_runtime_seconds <= 0 or time.monotonic() - started_at >= request.max_runtime_seconds:
                status = AutonomousSessionStatus.TIMEOUT
                break

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
                task_records,
                request.allow_dirty_start,
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

    def resume(self, session_path: Path) -> AutonomousSessionRecord:
        return SessionCheckpointStore.load(session_path)

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
        task_records: list[AutonomousTaskRecord],
        allow_dirty_start: bool,
        command_records: list[CommandRecord],
        commit_refs: list[str],
    ) -> AutonomousSessionStatus:
        status_record = self._git_status_without_bioclaw(workspace_path)
        command_records.append(status_record)
        if status_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED
        if not status_record.stdout.strip():
            return AutonomousSessionStatus.COMPLETED

        unstage_bioclaw_record = _run_shell("git restore --staged -- .bioclaw", cwd=workspace_path)
        command_records.append(unstage_bioclaw_record)
        if unstage_bioclaw_record.exit_code != 0:
            unstage_bioclaw_record = _run_shell(
                "git rm --cached --ignore-unmatch -r -- .bioclaw",
                cwd=workspace_path,
            )
            command_records.append(unstage_bioclaw_record)
            if unstage_bioclaw_record.exit_code != 0:
                return AutonomousSessionStatus.BLOCKED

        committable_paths = _committable_task_paths(task_records)
        dirty_paths = _status_paths_from_porcelain(status_record.stdout)
        unexpected_dirty_paths = tuple(path for path in dirty_paths if path not in committable_paths)
        if unexpected_dirty_paths and not allow_dirty_start:
            command_records.append(
                CommandRecord(
                    command="commit gate",
                    exit_code=1,
                    stdout="",
                    stderr="unexpected dirty paths outside completed write tasks: "
                    + ", ".join(unexpected_dirty_paths),
                )
            )
            return AutonomousSessionStatus.BLOCKED
        if not committable_paths:
            return AutonomousSessionStatus.COMPLETED

        add_record = _run_git(workspace_path, "add", "--", *committable_paths)
        command_records.append(add_record)
        if add_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED

        staged_record = _run_git(workspace_path, "diff", "--cached", "--name-only", "--", ".", ":!.bioclaw")
        command_records.append(staged_record)
        if not staged_record.stdout.strip():
            return AutonomousSessionStatus.COMPLETED
        staged_paths = tuple(line.strip() for line in staged_record.stdout.splitlines() if line.strip())
        unexpected_staged_paths = tuple(path for path in staged_paths if path not in committable_paths)
        if unexpected_staged_paths:
            command_records.append(
                CommandRecord(
                    command="commit gate",
                    exit_code=1,
                    stdout="",
                    stderr="unexpected staged paths outside completed write tasks: "
                    + ", ".join(unexpected_staged_paths),
                )
            )
            return AutonomousSessionStatus.BLOCKED

        commit_record = _run_git(
            workspace_path,
            "commit",
            "-m",
            f"Autonomous session {session_id} generation {generation_index}",
        )
        command_records.append(commit_record)
        if commit_record.exit_code != 0:
            return AutonomousSessionStatus.BLOCKED

        rev_parse_record = _run_git(workspace_path, "rev-parse", "HEAD")
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
        if _is_secret_read_command(tokens, command):
            return PolicyDecision.deny("secret read is denied by default")
        if _is_workspace_escape_command(tokens, workspace_path=self.workspace_path):
            return PolicyDecision.deny("command accesses paths outside workspace by default")
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


def _optional_int(payload: dict[str, Any], key: str, default: int) -> int:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
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
    if subcommand not in {"commit", "push"}:
        return False
    if not any(token in {"git", "git.exe"} for token in tokens):
        return False
    return subcommand in tokens


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


def _run_git(cwd: Path, *args: str) -> CommandRecord:
    command = "git " + " ".join(args)
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
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


def _committable_task_paths(task_records: list[AutonomousTaskRecord]) -> tuple[str, ...]:
    paths: list[str] = []
    for task_record in task_records:
        if task_record.operation is not AutonomousOperation.WRITE_FILE:
            continue
        if task_record.state != "completed":
            continue
        path = task_record.path.replace("\\", "/").strip("/")
        if not path or path.startswith(".bioclaw/") or path == ".bioclaw":
            continue
        paths.append(path)
    return tuple(dict.fromkeys(paths))


def _status_paths_from_porcelain(output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", maxsplit=1)[1]
        path = path.strip('"').replace("\\", "/")
        if path:
            paths.append(path)
    return tuple(paths)


_SECRET_HINTS = (
    "secret",
    "secrets",
    ".env",
    "credential",
    "credentials",
    "api_key",
    "apikey",
    "token",
    "passwd",
    "password",
    "private_key",
)


def _is_secret_token(text: str) -> bool:
    lowered = text.lower()
    if "openai_api_key" in lowered or "api_key" in lowered:
        return True
    if re.search(r"%[a-z0-9_]*(secret|token|key|password)[a-z0-9_]*%", lowered):
        return True
    if re.search(r"\$[a-z0-9_]*(secret|token|key|password)[a-z0-9_]*", lowered):
        return True
    return any(hint in lowered for hint in _SECRET_HINTS)


def _is_secret_read_command(tokens: tuple[str, ...], command: str) -> bool:
    if not tokens:
        return False
    verb = tokens[0]
    if verb in {"get-content", "type", "cat"}:
        return any(_is_secret_token(argument) for argument in tokens[1:])
    if verb in {"printenv", "env"}:
        return True
    if verb == "echo":
        return any(_is_secret_token(argument) for argument in tokens[1:])
    if "printenv" in command.lower():
        return True
    return False


def _looks_like_path(token: str) -> bool:
    return "\\" in token or "/" in token or re.search(r"^[a-zA-Z]:[\\\\/]", token) is not None


def _is_workspace_escape_command(tokens: tuple[str, ...], workspace_path: Path) -> bool:
    for token in tokens:
        candidate = token.strip("\"'`").strip()
        if not candidate or not _looks_like_path(candidate):
            continue
        if _is_parent_path_escape(candidate):
            return True
        normalized_candidate = candidate.replace("\\", "/")
        if _is_absolute_path(normalized_candidate):
            return not _is_in_workspace(Path(normalized_candidate).resolve(), workspace_path)
        return not _is_in_workspace((workspace_path / normalized_candidate).resolve(), workspace_path)
    return False


def _is_absolute_path(candidate: str) -> bool:
    return candidate.startswith("/") or candidate.startswith("\\\\") or re.match(r"^[a-zA-Z]:/", candidate) is not None


def _is_parent_path_escape(candidate: str) -> bool:
    normalized = candidate.replace("\\", "/")
    return normalized.startswith("../") or normalized.startswith("..//") or "/../" in normalized or normalized == ".."


def _is_in_workspace(candidate: Path, workspace_path: Path) -> bool:
    try:
        candidate.relative_to(workspace_path)
    except ValueError:
        return False
    return True


def _repo_has_local_fact(path: Path) -> bool:
    return path.exists()


def _seed_baseline_command(tests_path: Path) -> str:
    if tests_path.is_dir():
        return "python -m pytest -q"
    return 'python -c "print(\'no tests discovered\')"'


def _seed_gitignore_entries(workspace_path: Path) -> tuple[str, ...]:
    entries = [".bioclaw/"]
    if (workspace_path / "tests").is_dir() or (workspace_path / "pyproject.toml").exists():
        entries.extend(("__pycache__/", "*.py[cod]", ".pytest_cache/"))
    return tuple(entries)


def _is_gitignore_seed_ready(path: Path, required_entries: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    current = path.read_text(encoding="utf-8")
    existing_entries = {line.strip() for line in current.splitlines()}
    return all(entry in existing_entries for entry in required_entries)


def _append_seed_gitignore_entries(content: str, required_entries: tuple[str, ...]) -> str:
    rewritten = content
    if rewritten and not rewritten.endswith("\n"):
        rewritten += "\n"
    existing_entries = {line.strip() for line in rewritten.splitlines()}
    for entry in required_entries:
        if entry not in existing_entries:
            rewritten += f"{entry}\n"
    return rewritten
