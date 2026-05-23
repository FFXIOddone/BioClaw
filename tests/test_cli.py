import json
import subprocess

from bioscaffold.cli import main


def test_run_product_command_writes_delivery_report_json(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [
                    {
                        "requirement_id": "password-policy",
                        "text": "Require password policy.",
                        "artifact_type": "code",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["run-product", str(request_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["terminal_state"] == "archived"
    assert payload["archive_ref"] == "archive.organism_000001.000001"
    assert payload["assembly"]["capability_ref"] == "capability.organism_000001.v1"
    assert payload["validation"]["validated_refs"] == ["protein.password_policy.v1"]
    assert payload["project_microtask_count"] == 17


def test_run_product_command_can_write_report_to_file(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    output_path = tmp_path / "delivery-report.json"
    request_path.write_text(
        json.dumps(
            {
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [
                    {
                        "requirement_id": "password-policy",
                        "text": "Require password policy.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["run-product", str(request_path), "--output", str(output_path)])
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert payload["organism_id"] == "organism_000001"
    assert payload["task_ids"][0] == "task.workflow.birth.organism_000001"


def test_run_product_command_accepts_windows_utf8_bom_request(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [
                    {
                        "requirement_id": "password-policy",
                        "text": "Require password policy.",
                    }
                ],
            }
        ),
        encoding="utf-8-sig",
    )

    exit_code = main(["run-product", str(request_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["terminal_state"] == "archived"


def test_run_product_command_rejects_request_without_requirements(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "organism_id": "organism_000001",
                "product_name": "Authentication Module",
                "requirements": [],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["run-product", str(request_path)])

    assert exit_code == 2
    assert "requirements must contain at least one item" in capsys.readouterr().err


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
                        "content": "# Authentication Module\\n",
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
                        "content": "# Authentication Module\\n",
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


def test_resume_session_command_reads_session_json(tmp_path, capsys):
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
                        "content": "# Authentication Module\\n",
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

    exit_code = main(["resume-session", str(session_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["session_id"] == "session_000001"
    assert payload["status"] == "completed"


def test_run_session_command_rejects_invalid_json(tmp_path, capsys):
    request_path = tmp_path / "bad-request.json"
    request_path.write_text("{", encoding="utf-8")

    exit_code = main(["run-session", str(request_path)])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "Expecting" in stderr


def test_session_status_command_rejects_missing_file(tmp_path, capsys):
    exit_code = main(["session-status", str(tmp_path / "missing-session.json")])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "[Errno 2]" in stderr


def test_run_session_command_rejects_non_object_json_payload(tmp_path, capsys):
    request_path = tmp_path / "bad-request.json"
    request_path.write_text("[\"not-an-object\"]", encoding="utf-8")

    exit_code = main(["run-session", str(request_path)])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "request must be a JSON object" in stderr


def test_session_status_command_rejects_non_object_checkpoint_payload(tmp_path, capsys):
    session_path = tmp_path / "session.json"
    session_path.write_text("[\"not-an-object\"]", encoding="utf-8")

    exit_code = main(["session-status", str(session_path)])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "session data must be a JSON object" in stderr or "not a JSON object" in stderr


def test_run_session_command_pretty_outputs_multiline_json(tmp_path, capsys):
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
                        "content": "# Authentication Module\\n",
                    }
                ],
                "verification_commands": [],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["run-session", str(request_path), "--pretty"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert '\n  "' in out
    payload = json.loads(out)
    assert payload["status"] == "completed"


def test_run_seed_command_runs_seeded_workflow(tmp_path, capsys):
    workspace = tmp_path / "project"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "bioclaw@example.local"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "BioClaw"], cwd=workspace, check=True)
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    request = {
        "session_id": "seed_session_000001",
        "workspace_path": str(workspace),
        "organism_id": "organism_000001",
        "product_name": "Seeded Automation Baseline",
        "seed_goal": "Prepare baseline and ensure smoke tests pass.",
        "generation_limit": 3,
        "verification_commands": [],
        "allow_dirty_start": True,
    }
    request_path = tmp_path / "seed-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    exit_code = main(["run-seed", str(request_path), "--pretty"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "completed"
    seed_summary_path = workspace / ".bioclaw" / "seeds" / "seed_session_000001" / "seed-session.json"
    assert seed_summary_path.exists()


def test_run_seed_command_rejects_invalid_json(tmp_path, capsys):
    request_path = tmp_path / "bad-seed-request.json"
    request_path.write_text("{", encoding="utf-8")

    exit_code = main(["run-seed", str(request_path)])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "Expecting" in stderr


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


def test_session_status_command_pretty_outputs_multiline_json(tmp_path, capsys):
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
                        "content": "# Authentication Module\\n",
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

    exit_code = main(["session-status", str(session_path), "--pretty"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert '\n  "' in out
    payload = json.loads(out)
    assert payload["status"] == "completed"


def test_cli_requires_a_command(capsys):
    exit_code = main([])
    stderr = capsys.readouterr().err

    assert exit_code == 2
    assert "usage:" in stderr
