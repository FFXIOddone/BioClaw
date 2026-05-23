from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from bioscaffold.all_generation import AllGenerationProductRunner, ProductBuildRequest
from bioscaffold.autonomy import (
    AutonomousSessionController,
    AutonomousSessionRequest,
    SeedAutonomousController,
    SeedAutonomousRequest,
    default_biological_fleet,
)
from bioscaffold.compiler import ProductRequirement
from bioscaffold.immune import PathogenFixture


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run-product":
        return _run_product(args)
    if args.command == "run-session":
        return _run_session(args)
    if args.command == "run-seed":
        return _run_seed(args)
    if args.command == "fleet-manifest":
        return _fleet_manifest(args)
    if args.command == "resume-session":
        return _resume_session(args)
    if args.command == "session-status":
        return _session_status(args)
    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bioscaffold",
        description="Run BioScaffold product workflow commands.",
    )
    subparsers = parser.add_subparsers(dest="command")
    run_product = subparsers.add_parser(
        "run-product",
        help="Run a product build request through the all-generation workflow.",
    )
    run_product.add_argument(
        "request",
        type=Path,
        help="Path to a product build request JSON file.",
    )
    run_product.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the delivery report JSON. Defaults to stdout.",
    )
    run_product.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    run_session = subparsers.add_parser(
        "run-session",
        help="Run a local-only autonomous project session.",
    )
    run_session.add_argument(
        "request",
        type=Path,
        help="Path to an autonomous session request JSON file.",
    )
    run_session.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    run_seed = subparsers.add_parser(
        "run-seed",
        help="Run a seeded autonomous workflow request.",
    )
    run_seed.add_argument(
        "request",
        type=Path,
        help="Path to a seeded autonomous request JSON file.",
    )
    run_seed.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    fleet_manifest = subparsers.add_parser(
        "fleet-manifest",
        help="Print the default biological fleet manifest JSON.",
    )
    fleet_manifest.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    resume_session = subparsers.add_parser(
        "resume-session",
        help="Resume by reading an autonomous session checkpoint.",
    )
    resume_session.add_argument(
        "session",
        type=Path,
        help="Path to a saved session JSON checkpoint.",
    )
    resume_session.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    session_status = subparsers.add_parser(
        "session-status",
        help="Print autonomous session checkpoint status JSON.",
    )
    session_status.add_argument(
        "session",
        type=Path,
        help="Path to a saved session JSON checkpoint.",
    )
    session_status.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with two-space indentation.",
    )
    return parser


def _run_product(args: argparse.Namespace) -> int:
    try:
        request = _load_request(args.request)
        result = AllGenerationProductRunner().run(request)
        payload = _result_payload(result)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report_json = _as_json(payload, pretty=args.pretty)
    if args.output is None:
        print(report_json)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(f"{report_json}\n", encoding="utf-8")
    return 0


def _print_json(payload: dict[str, Any], *, pretty: bool) -> None:
    print(_as_json(payload, pretty=pretty))


def _as_json(payload: dict[str, Any], *, pretty: bool) -> str:
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=True)


def _read_json_object(path: Path, *, context: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be a JSON object")
    return payload


def _run_session(args: argparse.Namespace) -> int:
    try:
        payload = _read_json_object(args.request, context="request")
        request = AutonomousSessionRequest.from_payload(payload)
        record = AutonomousSessionController().run(request)
    except (AttributeError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(record.to_payload(), pretty=args.pretty)
    return 0


def _run_seed(args: argparse.Namespace) -> int:
    try:
        payload = _read_json_object(args.request, context="request")
        request = SeedAutonomousRequest.from_payload(payload)
        record = SeedAutonomousController().run(request)
    except (AttributeError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(record.to_payload(), pretty=args.pretty)
    return 0


def _fleet_manifest(args: argparse.Namespace) -> int:
    fleet = default_biological_fleet()
    _print_json(
        {
            "enable_structure_fleet": True,
            "fleet_count": len(fleet),
            "structure_fleet": [unit.to_payload() for unit in fleet],
        },
        pretty=args.pretty,
    )
    return 0


def _resume_session(args: argparse.Namespace) -> int:
    try:
        _read_json_object(args.session, context="session data")
        record = AutonomousSessionController().resume(args.session)
    except (AttributeError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(record.to_payload(), pretty=args.pretty)
    return 0


def _session_status(args: argparse.Namespace) -> int:
    return _resume_session(args)


def _load_request(path: Path) -> ProductBuildRequest:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("request must be a JSON object")
    requirements = _requirements(raw.get("requirements"))
    return ProductBuildRequest(
        organism_id=_required_string(raw, "organism_id"),
        product_name=_required_string(raw, "product_name"),
        requirements=requirements,
        known_immune_markers=_string_tuple(
            raw.get("known_immune_markers", ()),
            "known_immune_markers",
        ),
        pathogen_fixtures_by_generation=_pathogen_fixtures_by_generation(
            raw.get("pathogen_fixtures_by_generation", ()),
        ),
    )


def _requirements(raw: Any) -> tuple[ProductRequirement, ...]:
    if not isinstance(raw, list):
        raise ValueError("requirements must be a list")
    if not raw:
        raise ValueError("requirements must contain at least one item")
    requirements = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"requirements[{index}] must be an object")
        requirements.append(
            ProductRequirement(
                requirement_id=_required_string(item, "requirement_id", f"requirements[{index}]"),
                text=_required_string(item, "text", f"requirements[{index}]"),
                artifact_type=_optional_string(
                    item,
                    "artifact_type",
                    default="code",
                    context=f"requirements[{index}]",
                ),
                markers=_string_tuple(
                    item.get("markers", ()),
                    f"requirements[{index}].markers",
                ),
            )
        )
    return tuple(requirements)


def _pathogen_fixtures_by_generation(raw: Any) -> tuple[tuple[PathogenFixture, ...], ...]:
    if raw in (None, ()):
        return ()
    if not isinstance(raw, list):
        raise ValueError("pathogen_fixtures_by_generation must be a list")
    generations = []
    for generation_index, generation in enumerate(raw):
        if not isinstance(generation, list):
            raise ValueError(
                f"pathogen_fixtures_by_generation[{generation_index}] must be a list"
            )
        fixtures = []
        for fixture_index, item in enumerate(generation):
            context = f"pathogen_fixtures_by_generation[{generation_index}][{fixture_index}]"
            if not isinstance(item, dict):
                raise ValueError(f"{context} must be an object")
            fixtures.append(
                PathogenFixture(
                    fixture_id=_required_string(item, "fixture_id", context),
                    defect_marker=_required_string(item, "defect_marker", context),
                    injected_ref=_required_string(item, "injected_ref", context),
                    payload=_required_string(item, "payload", context),
                )
            )
        generations.append(tuple(fixtures))
    return tuple(generations)


def _result_payload(result: Any) -> dict[str, Any]:
    report = result.delivery_report
    return {
        "organism_id": report.organism_id,
        "terminal_state": report.terminal_state.value,
        "archive_ref": report.archive_ref,
        "delivered_outputs": list(report.delivered_outputs),
        "generation_ids": list(report.generation_ids),
        "task_ids": list(report.task_ids),
        "immune_event_ids": list(report.immune_event_ids),
        "proposal_task_ids": list(report.proposal_task_ids),
        "validation_task_ids": list(report.validation_task_ids),
        "project_microtask_count": len(result.project_microtasks),
        "validation": {
            "validated_refs": list(result.validation.validated_refs),
            "quarantined_refs": list(result.validation.quarantined_refs),
            "antibody_refs": list(result.validation.antibody_refs),
        },
        "assembly": {
            "module_ref": result.assembly.module_ref,
            "subsystem_ref": result.assembly.subsystem_ref,
            "capability_ref": result.assembly.capability_ref,
            "assembly_refs": list(report.assembly_refs),
        },
    }


def _required_string(raw: dict[str, Any], key: str, context: str = "request") -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _optional_string(
    raw: dict[str, Any],
    key: str,
    *,
    default: str,
    context: str,
) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _string_tuple(raw: Any, context: str) -> tuple[str, ...]:
    if raw in (None, ()):
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{context} must be a list")
    values = []
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}[{index}] must be a non-empty string")
        values.append(item)
    return tuple(values)
