import json

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
