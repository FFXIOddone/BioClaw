import json
import subprocess

import pytest

from bioscaffold.autonomy import (
    AutonomousSessionController,
    AutonomousSessionRecord,
    AutonomousSessionStatus,
    AutonomousOperation,
    AutonomousPolicy,
    AutonomousSessionRequest,
    AutonomousTaskRecord,
    CommandRecord,
    SessionCheckpointStore,
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


def test_autonomous_request_rejects_non_boolean_policy_flags(tmp_path):
    payload = _request_payload(tmp_path)

    for key in ("allow_local_edits", "allow_local_commits", "allow_push", "allow_dirty_start"):
        invalid_payload = {**payload, key: "false"}
        with pytest.raises(ValueError, match=key):
            AutonomousSessionRequest.from_payload(invalid_payload)


def test_autonomous_policy_enforces_path_containment_for_file_operations(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        AutonomousWorkItem("task.inspect", AutonomousOperation.INSPECT_FILE, path="../secrets.txt"),
        AutonomousWorkItem("task.write", AutonomousOperation.WRITE_FILE, path="../secrets.txt"),
        AutonomousWorkItem("task.record", AutonomousOperation.RECORD, path="../secrets.txt"),
    ]

    for item in denied:
        decision = policy.authorize(item)
        assert decision.allowed is False
        assert decision.reason == "path escapes workspace"


def test_autonomous_policy_denies_git_commit_until_commit_gate_exists(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    decision = policy.authorize(AutonomousWorkItem("task.commit", AutonomousOperation.GIT_COMMIT))

    assert decision.allowed is False
    assert decision.reason


def test_autonomous_work_item_rejects_present_non_string_optional_fields():
    with pytest.raises(ValueError, match="project_tasks\\[\\].command"):
        AutonomousWorkItem.from_payload(
            {
                "task_id": "task.command",
                "operation": "run_command",
                "command": None,
            }
        )


def test_autonomous_request_rejects_string_verification_commands(tmp_path):
    payload = {**_request_payload(tmp_path), "verification_commands": "pytest"}

    with pytest.raises(ValueError, match="verification_commands"):
        AutonomousSessionRequest.from_payload(payload)


def test_autonomous_policy_denies_windows_command_bypasses(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        AutonomousWorkItem("task.git_exe_push", AutonomousOperation.RUN_COMMAND, command="git.exe push origin main"),
        AutonomousWorkItem("task.tab_delete", AutonomousOperation.RUN_COMMAND, command="Remove-Item\t-Recurse ."),
        AutonomousWorkItem("task.erase", AutonomousOperation.RUN_COMMAND, command="erase README.md"),
        AutonomousWorkItem("task.rd", AutonomousOperation.RUN_COMMAND, command="rd /s build"),
    ]

    for item in denied:
        decision = policy.authorize(item)
        assert decision.allowed is False
        assert decision.reason


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
        task_records=(
            AutonomousTaskRecord(
                task_id="task.write.readme",
                operation=AutonomousOperation.WRITE_FILE,
                state="completed",
                reason="wrote README.md",
                path="README.md",
                outputs=("README.md",),
            ),
        ),
        command_records=(
            CommandRecord(
                command="python -m pytest tests/test_autonomous_session.py",
                exit_code=0,
                stdout="1 passed",
                stderr="",
            ),
        ),
        commit_refs=("abc1234",),
    )

    store.write_checkpoint(record)

    assert (store.session_dir / "session.json").exists()
    assert (store.session_dir / "generation_000001.json").exists()
    assert (store.session_dir / "task_log.jsonl").exists()
    assert (store.session_dir / "command_log.jsonl").exists()
    assert json.loads((store.session_dir / "session.json").read_text(encoding="utf-8"))["status"] == "running"
    task_lines = (store.session_dir / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
    command_lines = (store.session_dir / "command_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(task_lines[0])["task_id"] == "task.write.readme"
    assert json.loads(command_lines[0])["exit_code"] == 0


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
        task_records=(
            AutonomousTaskRecord(
                task_id="task.write.readme",
                operation=AutonomousOperation.WRITE_FILE,
                state="completed",
                reason="wrote README.md",
                path="README.md",
                outputs=("README.md",),
            ),
        ),
        command_records=(
            CommandRecord(
                command="python -m pytest tests/test_autonomous_session.py",
                exit_code=0,
                stdout="1 passed",
                stderr="",
            ),
        ),
        commit_refs=("abc1234",),
    )
    store.write_checkpoint(record)

    resumed = SessionCheckpointStore.load(store.session_dir / "session.json")

    assert resumed.session_id == "session_000001"
    assert resumed.status is AutonomousSessionStatus.COMPLETED
    assert resumed.generation_index == 1
    assert resumed.task_records == record.task_records
    assert resumed.command_records == record.command_records
    assert resumed.commit_refs == ("abc1234",)


def test_checkpoint_store_rejects_unsafe_session_ids(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()

    for session_id in ("../escape", "nested/session", str(tmp_path / "absolute")):
        with pytest.raises(ValueError, match="session_id"):
            SessionCheckpointStore(workspace, session_id)


def test_checkpoint_store_rejects_mismatched_record_identity_and_negative_generation(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    store = SessionCheckpointStore(workspace, "session_000001")

    invalid_records = [
        _session_record(workspace, store, session_id="session_000002"),
        _session_record(tmp_path / "other", store),
        _session_record(workspace, store, generation_index=-1),
    ]

    for record in invalid_records:
        with pytest.raises(ValueError):
            store.write_checkpoint(record)


def test_checkpoint_store_rewrites_complete_logs_from_record_history(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    store = SessionCheckpointStore(workspace, "session_000001")
    first_task = AutonomousTaskRecord(
        task_id="task.inspect",
        operation=AutonomousOperation.INSPECT_FILE,
        state="completed",
        reason="read README.md",
        path="README.md",
    )
    second_task = AutonomousTaskRecord(
        task_id="task.write",
        operation=AutonomousOperation.WRITE_FILE,
        state="completed",
        reason="wrote README.md",
        path="README.md",
    )
    first_command = CommandRecord(command="python -m pytest first", exit_code=0, stdout="1 passed", stderr="")
    second_command = CommandRecord(command="python -m pytest second", exit_code=0, stdout="2 passed", stderr="")

    store.write_checkpoint(
        _session_record(
            workspace,
            store,
            generation_index=1,
            task_records=(first_task,),
            command_records=(first_command,),
        )
    )
    store.write_checkpoint(
        _session_record(
            workspace,
            store,
            generation_index=2,
            task_records=(first_task, second_task),
            command_records=(first_command, second_command),
        )
    )

    task_lines = (store.session_dir / "task_log.jsonl").read_text(encoding="utf-8").splitlines()
    command_lines = (store.session_dir / "command_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["task_id"] for line in task_lines] == ["task.inspect", "task.write"]
    assert [json.loads(line)["command"] for line in command_lines] == [
        "python -m pytest first",
        "python -m pytest second",
    ]


def test_autonomous_session_writes_file_verifies_and_commits_generation(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": [
                "python -c \"from pathlib import Path; assert Path('README.md').read_text(encoding='utf-8') == '# Demo\\n'\""
            ],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.COMPLETED
    assert (workspace / "README.md").read_text(encoding="utf-8") == "# Demo\n"
    assert len(record.commit_refs) == 1
    assert _git(workspace, "rev-parse", "HEAD").stdout.strip() == record.commit_refs[0]
    assert _git(workspace, "rev-list", "--count", "HEAD").stdout.strip() == "1"
    assert (workspace / ".bioclaw" / "sessions" / "session_000001" / "session.json").exists()


def test_autonomous_session_blocks_commit_when_verification_fails(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": ["python -c \"raise SystemExit(7)\""],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.BLOCKED
    assert record.commit_refs == ()
    assert any(command.exit_code == 7 for command in record.command_records)
    assert _git(workspace, "rev-parse", "--verify", "HEAD", check=False).returncode != 0
    assert (workspace / ".bioclaw" / "sessions" / "session_000001" / "session.json").exists()


def init_git_repo(workspace):
    _git(workspace, "init")
    _git(workspace, "config", "user.email", "test@example.invalid")
    _git(workspace, "config", "user.name", "BioClaw Test")


def _git(workspace, *args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=workspace,
        check=check,
        text=True,
        capture_output=True,
    )


def _session_record(
    workspace,
    store,
    *,
    session_id="session_000001",
    generation_index=1,
    task_records=(),
    command_records=(),
):
    return AutonomousSessionRecord(
        session_id=session_id,
        workspace_path=str(workspace),
        organism_id="organism_000001",
        product_name="Authentication Module",
        status=AutonomousSessionStatus.RUNNING,
        max_runtime_seconds=28800,
        generation_index=generation_index,
        checkpoint_dir=str(store.session_dir),
        task_records=task_records,
        command_records=command_records,
    )


def _request_payload(tmp_path):
    return {
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
