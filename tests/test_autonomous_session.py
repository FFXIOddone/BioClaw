import pytest

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
