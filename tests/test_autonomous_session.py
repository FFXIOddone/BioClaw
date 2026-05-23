import json
import subprocess
from pathlib import Path

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
    SeedAutonomousRequest,
    SeedGenerationPlan,
    SeedGenerationStatus,
    SeedGenerationRecord,
    SeedAutonomousController,
    SeedAutonomousRecord,
    SeedMicrotaskPlanner,
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


def test_seed_autonomous_request_defaults_to_expected_values(tmp_path):
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(tmp_path),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )

    assert request.max_runtime_seconds == 28800
    assert request.generation_limit == 4
    assert request.allow_local_edits is True
    assert request.allow_local_commits is True
    assert request.allow_push is False
    assert request.allow_dirty_start is False
    assert request.verification_commands == ()


def test_seed_planner_writes_gitignore_when_missing(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )
    planner = SeedMicrotaskPlanner()
    plan = planner.plan_generation(request, generation_index=1)

    assert isinstance(plan, SeedGenerationPlan)
    assert plan.generation_index == 1
    assert plan.is_terminal is False
    assert len(plan.verification_commands) == 1
    assert len(plan.project_tasks) >= 1
    assert plan.project_tasks[0].operation is AutonomousOperation.WRITE_FILE
    assert plan.project_tasks[0].path == ".gitignore"
    assert plan.project_tasks[0].content == ".bioclaw/\n"
    assert plan.project_tasks[1].operation is AutonomousOperation.RUN_COMMAND
    assert plan.project_tasks[1].command == "python -c \"print('no tests discovered')\""
    assert plan.verification_commands[0] == "python -c \"print('no tests discovered')\""


def test_seed_planner_appends_bioclaw_to_existing_gitignore(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".gitignore").write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )
    planner = SeedMicrotaskPlanner()
    plan = planner.plan_generation(request, generation_index=1)

    assert plan.is_terminal is False
    assert plan.project_tasks[0].operation is AutonomousOperation.WRITE_FILE
    assert plan.project_tasks[0].path == ".gitignore"
    assert plan.project_tasks[0].content == "*.pyc\n__pycache__/\n.bioclaw/\n"
    assert plan.project_tasks[1].operation is AutonomousOperation.RUN_COMMAND
    assert plan.project_tasks[1].command == "python -c \"print('no tests discovered')\""


def test_seed_planner_uses_baseline_verification_when_not_provided(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "tests").mkdir()
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )
    planner = SeedMicrotaskPlanner()
    plan = planner.plan_generation(request, generation_index=1)

    assert plan.verification_commands == ("python -m pytest -q",)


def test_seed_planner_prefers_request_verification_commands(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "verification_commands": ("python -c \"print('custom')\"",),
        }
    )
    planner = SeedMicrotaskPlanner()
    plan = planner.plan_generation(request, generation_index=1)

    assert plan.verification_commands == ("python -c \"print('custom')\"",)


def test_seed_planner_returns_terminal_when_bioclaw_already_ignored(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".gitignore").write_text(".bioclaw/\n", encoding="utf-8")
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )
    planner = SeedMicrotaskPlanner()
    plan = planner.plan_generation(request, generation_index=2)

    assert plan.is_terminal is True
    assert plan.project_tasks == ()
    assert plan.verification_commands == ()


def test_seed_autonomous_request_rejects_non_int_runtime_and_limit_fields(tmp_path):
    payload = {
        "session_id": "seed_session_000001",
        "workspace_path": str(tmp_path),
        "organism_id": "organism_seed",
        "product_name": "Seed Baseline",
        "seed_goal": "Prepare repository for deterministic autonomous seeding.",
    }

    with pytest.raises(ValueError, match="max_runtime_seconds"):
        SeedAutonomousRequest.from_payload({**payload, "max_runtime_seconds": "3600"})

    with pytest.raises(ValueError, match="max_runtime_seconds"):
        SeedAutonomousRequest.from_payload({**payload, "max_runtime_seconds": True})

    with pytest.raises(ValueError, match="generation_limit"):
        SeedAutonomousRequest.from_payload({**payload, "generation_limit": "4"})

    with pytest.raises(ValueError, match="generation_limit"):
        SeedAutonomousRequest.from_payload({**payload, "generation_limit": False})


def test_seed_plan_record_payload_is_json_friendly_with_serialized_enums(tmp_path):
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(tmp_path),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
        }
    )
    plan = SeedMicrotaskPlanner().plan_generation(request, generation_index=1)

    generation_record = SeedGenerationRecord(
        generation_index=plan.generation_index,
        project_tasks=plan.project_tasks,
        verification_commands=plan.verification_commands,
        status=SeedGenerationStatus.BLOCKED,
        terminal=False,
    )
    seed_record = SeedAutonomousRecord(
        session_id=request.session_id,
        workspace_path=str(request.workspace_path),
        organism_id=request.organism_id,
        product_name=request.product_name,
        seed_goal=request.seed_goal,
        status=SeedGenerationStatus.POLICY_DENIED,
        generation_limit=request.generation_limit,
        max_runtime_seconds=request.max_runtime_seconds,
        generations=(generation_record,),
    )

    plan_payload = plan.to_payload()
    record_payload = generation_record.to_payload()
    seed_payload = seed_record.to_payload()

    json.dumps(plan_payload)
    json.dumps(record_payload)
    json.dumps(seed_payload)

    assert plan_payload["project_tasks"] == [
        {
            "task_id": f"seed_generation_{plan.generation_index:06d}.gitignore",
            "operation": "write_file",
            "path": ".gitignore",
            "content": ".bioclaw/\n",
            "command": "",
            "expected_output": "",
        },
    ] + [
        {
            "task_id": f"seed_generation_{plan.generation_index:06d}.baseline",
            "operation": "run_command",
            "path": "",
            "content": "",
            "command": "python -c \"print('no tests discovered')\"",
            "expected_output": "",
        }
    ]
    assert plan_payload["is_terminal"] is False
    assert record_payload["status"] == SeedGenerationStatus.BLOCKED.value
    assert record_payload["project_tasks"][0]["operation"] == "write_file"
    assert seed_payload["status"] == SeedGenerationStatus.POLICY_DENIED.value
    assert seed_payload["generations"][0]["status"] == SeedGenerationStatus.BLOCKED.value


def test_seed_autonomous_controller_writes_seed_summary_and_stops_on_terminal_plan(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "generation_limit": 4,
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.COMPLETED
    assert record.generations
    assert len(record.generations) >= 2
    assert record.generations[0].status is SeedGenerationStatus.COMPLETED
    assert record.generations[0].inner_checkpoint_path
    assert record.generations[1].status is SeedGenerationStatus.COMPLETED
    assert record.generations[1].terminal

    summary_path = workspace / ".bioclaw" / "seeds" / request.session_id / "seed-session.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["status"] == SeedGenerationStatus.COMPLETED.value
    assert payload["generations"][0]["inner_checkpoint_path"] == record.generations[0].inner_checkpoint_path


def test_seed_autonomous_controller_does_not_commit_or_leave_pytest_artifacts(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert True\n",
        encoding="utf-8",
    )
    _git(workspace, "add", "tests/test_smoke.py")
    _git(workspace, "commit", "-m", "Baseline test suite")
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "generation_limit": 3,
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.COMPLETED
    committed_files = _git(workspace, "show", "--name-only", "--format=", "HEAD").stdout.splitlines()
    assert committed_files == [".gitignore"]
    dirty_after_seed = _git(
        workspace,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        ".",
        ":!.bioclaw",
    ).stdout
    assert dirty_after_seed == ""


def test_seed_autonomous_controller_limits_out_when_no_generation_capacity(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "generation_limit": 0,
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.GENERATION_LIMIT_REACHED
    assert record.generations == ()

    summary_path = workspace / ".bioclaw" / "seeds" / request.session_id / "seed-session.json"
    assert summary_path.exists()
    assert json.loads(summary_path.read_text(encoding="utf-8"))["status"] == SeedGenerationStatus.GENERATION_LIMIT_REACHED.value


def test_seed_autonomous_controller_propagates_inner_blocked_status(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "verification_commands": [
                "python -c \"import sys; sys.exit(1)\"",
            ],
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.BLOCKED
    assert len(record.generations) == 1
    assert record.generations[0].status is SeedGenerationStatus.BLOCKED
    assert record.generations[0].inner_status == AutonomousSessionStatus.BLOCKED.value


def test_seed_autonomous_controller_propagates_inner_policy_denied_status(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "verification_commands": [
                "git push origin main",
            ],
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.POLICY_DENIED
    assert len(record.generations) == 1
    assert record.generations[0].status is SeedGenerationStatus.POLICY_DENIED
    assert record.generations[0].inner_status == AutonomousSessionStatus.POLICY_DENIED.value


def test_seed_autonomous_controller_propagates_inner_timeout_status(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = SeedAutonomousRequest.from_payload(
        {
            "session_id": "seed_session_000001",
            "workspace_path": str(workspace),
            "organism_id": "organism_seed",
            "product_name": "Seed Baseline",
            "seed_goal": "Prepare repository for deterministic autonomous seeding.",
            "max_runtime_seconds": 0,
        }
    )

    record = SeedAutonomousController().run(request)

    assert record.status is SeedGenerationStatus.TIMEOUT
    assert len(record.generations) == 1
    assert record.generations[0].status is SeedGenerationStatus.TIMEOUT
    assert record.generations[0].inner_status == AutonomousSessionStatus.TIMEOUT.value


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


def test_autonomous_policy_denies_secret_read_commands(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        "Get-Content .env",
        "type .env",
        "cat secrets.txt",
        "printenv OPENAI_API_KEY",
        "echo %API_KEY%",
        "echo $OPENAI_API_KEY",
    ]

    for command in denied:
        decision = policy.authorize(AutonomousWorkItem("task.secret", AutonomousOperation.RUN_COMMAND, command=command))
        assert decision.allowed is False
        assert decision.reason


def test_autonomous_policy_denies_commands_with_obvious_path_escape_targets(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        "python ..\\outside.py",
        "type ..\\secret.txt",
        "Get-Content ..\\secret.txt",
        "python ../outside.py",
        "python /tmp/outside.py",
        "python C:\\Windows\\System32\\cmd.exe",
    ]

    for command in denied:
        decision = policy.authorize(AutonomousWorkItem("task.path", AutonomousOperation.RUN_COMMAND, command=command))
        assert decision.allowed is False
        assert decision.reason


def test_autonomous_policy_allows_safe_verification_commands(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    decision = policy.authorize(
        AutonomousWorkItem(
            "task.verify",
            AutonomousOperation.RUN_COMMAND,
            command="python -c \"print('ok')\"",
        )
    )

    assert decision.allowed is True


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


def test_autonomous_policy_denies_run_command_git_commit_bypasses(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        AutonomousWorkItem("task.git_commit", AutonomousOperation.RUN_COMMAND, command="git commit -m bypass"),
        AutonomousWorkItem("task.git_exe_commit", AutonomousOperation.RUN_COMMAND, command="git.exe commit -m bypass"),
        AutonomousWorkItem(
            "task.git_flag_commit",
            AutonomousOperation.RUN_COMMAND,
            command="git -c foo=bar commit --allow-empty -m bypass",
        ),
        AutonomousWorkItem(
            "task.git_exe_flag_commit",
            AutonomousOperation.RUN_COMMAND,
            command="git.exe -c foo=bar commit --allow-empty -m bypass",
        ),
    ]

    for item in denied:
        decision = policy.authorize(item)
        assert decision.allowed is False
        assert decision.reason


def test_autonomous_policy_denies_run_command_git_push_bypasses(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path)

    denied = [
        AutonomousWorkItem("task.git_push", AutonomousOperation.RUN_COMMAND, command="git push origin main"),
        AutonomousWorkItem(
            "task.git_flag_push",
            AutonomousOperation.RUN_COMMAND,
            command="git -c foo=bar push origin main",
        ),
        AutonomousWorkItem(
            "task.git_exe_flag_push",
            AutonomousOperation.RUN_COMMAND,
            command="git.exe -c foo=bar push origin main",
        ),
    ]

    for item in denied:
        decision = policy.authorize(item)
        assert decision.allowed is False
        assert decision.reason


def test_autonomous_policy_allows_git_push_with_allow_push_true(tmp_path):
    policy = AutonomousPolicy.default(workspace_path=tmp_path, allow_push=True)

    allowed = [
        AutonomousWorkItem("task.git_push_allowed", AutonomousOperation.RUN_COMMAND, command="git push origin main"),
        AutonomousWorkItem(
            "task.git_flag_push_allowed",
            AutonomousOperation.RUN_COMMAND,
            command="git -c foo=bar push origin main",
        ),
        AutonomousWorkItem(
            "task.git_exe_flag_push_allowed",
            AutonomousOperation.RUN_COMMAND,
            command="git.exe -c foo=bar push origin main",
        ),
    ]

    for item in allowed:
        decision = policy.authorize(item)
        assert decision.allowed is True


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


def test_autonomous_session_blocks_dirty_start_when_not_allowed(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": [],
        }
    )

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
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": [],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.COMPLETED
    committed_files = _git(workspace, "show", "--name-only", "--format=", "HEAD").stdout.splitlines()
    assert "README.md" in committed_files
    assert all(not path.startswith(".bioclaw/") for path in committed_files)


def test_autonomous_session_unstages_staged_bioclaw_checkpoint_noise_before_commit(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / ".bioclaw" / "sessions" / "old").mkdir(parents=True)
    checkpoint_noise = workspace / ".bioclaw" / "sessions" / "old" / "session.json"
    checkpoint_noise.write_text("{}", encoding="utf-8")
    _git(workspace, "add", str(checkpoint_noise))
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": [],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.COMPLETED
    committed_files = _git(workspace, "show", "--name-only", "--format=", "HEAD").stdout.splitlines()
    assert "README.md" in committed_files
    assert all(not path.startswith(".bioclaw/") for path in committed_files)


def test_autonomous_session_skips_commit_when_only_checkpoint_noise_staged(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    (workspace / ".bioclaw" / "sessions" / "old").mkdir(parents=True)
    checkpoint_noise = workspace / ".bioclaw" / "sessions" / "old" / "session.json"
    checkpoint_noise.write_text("{}", encoding="utf-8")
    _git(workspace, "add", str(checkpoint_noise))
    request = AutonomousSessionRequest.from_payload(
        {
            "session_id": "session_000001",
            "workspace_path": str(workspace),
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
                    "task_id": "task.verify.only",
                    "operation": "run_command",
                    "command": "python -c \"print('ok')\"",
                },
            ],
            "verification_commands": [],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.COMPLETED
    assert record.commit_refs == ()
    assert _git(workspace, "rev-list", "--count", "HEAD", check=False).returncode == 128


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


def test_autonomous_session_denies_run_command_git_commit_and_does_not_commit(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "project_tasks": [
                {
                    "task_id": "task.commit.bypass",
                    "operation": "run_command",
                    "command": "git commit --allow-empty -m bypass",
                }
            ],
            "verification_commands": [],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.POLICY_DENIED
    assert record.commit_refs == ()
    assert record.task_records[0].state == AutonomousSessionStatus.POLICY_DENIED.value
    assert _git(workspace, "rev-parse", "--verify", "HEAD", check=False).returncode != 0


def test_autonomous_session_denies_verification_git_commit_and_does_not_commit(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "verification_commands": ["git commit --allow-empty -m verify-bypass"],
        }
    )

    record = AutonomousSessionController().run(request)

    assert record.status is AutonomousSessionStatus.POLICY_DENIED
    assert record.commit_refs == ()
    assert any(command.command == "git commit --allow-empty -m verify-bypass" for command in record.command_records)
    assert _git(workspace, "rev-parse", "--verify", "HEAD", check=False).returncode != 0


def test_autonomous_session_records_timeout_before_work(tmp_path):
    workspace = tmp_path / "project"
    workspace.mkdir()
    init_git_repo(workspace)
    request = AutonomousSessionRequest.from_payload(
        {
            **_request_payload(workspace),
            "max_runtime_seconds": 0,
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
            **_request_payload(workspace),
            "verification_commands": [],
        }
    )
    original = AutonomousSessionController().run(request)

    resumed = AutonomousSessionController().resume(Path(original.checkpoint_dir) / "session.json")

    assert resumed.session_id == original.session_id
    assert resumed.status is AutonomousSessionStatus.COMPLETED


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
