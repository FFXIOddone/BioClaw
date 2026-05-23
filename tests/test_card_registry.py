from pathlib import Path

import pytest

from bioscaffold.cards import BioComponentCard, load_card, load_registry


VALID_CARD = {
    "bio_component": {
        "name": "nucleus",
        "scale": "organelle",
        "biological_role": "Houses genome and coordinates control.",
        "software_role": "Governance kernel.",
        "implementation_status": "planned",
        "inputs": ["cell_state"],
        "outputs": ["policy_decision"],
        "internal_state": {"identity": "cell identity"},
        "sensors": ["health_score"],
        "control_rules": ["reject unauthorized actions"],
        "repair_rules": ["quarantine invalid policy state"],
        "recycle_rules": ["forward stale data to lysosome"],
        "replication_rules": ["require checkpoint pass"],
        "failure_modes": ["permission escalation"],
        "safety_limits": {"production_access": False},
        "tests_required": ["test_rejects_permission_escalation"],
        "shutdown_condition": "policy corruption",
        "human_review_required": True,
    }
}


def test_card_validates_required_fields():
    card = BioComponentCard.model_validate(VALID_CARD["bio_component"])

    assert card.name == "nucleus"
    assert card.scale == "organelle"
    assert card.human_review_required is True


def test_card_rejects_empty_safety_limits():
    invalid = dict(VALID_CARD["bio_component"])
    invalid["safety_limits"] = {}

    with pytest.raises(ValueError, match="safety_limits"):
        BioComponentCard.model_validate(invalid)


def test_load_card_reads_yaml(tmp_path: Path):
    path = tmp_path / "nucleus.yaml"
    path.write_text(
        """
bio_component:
  name: nucleus
  scale: organelle
  biological_role: Houses genome and coordinates control.
  software_role: Governance kernel.
  implementation_status: planned
  inputs: [cell_state]
  outputs: [policy_decision]
  internal_state:
    identity: cell identity
  sensors: [health_score]
  control_rules: [reject unauthorized actions]
  repair_rules: [quarantine invalid policy state]
  recycle_rules: [forward stale data to lysosome]
  replication_rules: [require checkpoint pass]
  failure_modes: [permission escalation]
  safety_limits:
    production_access: false
  tests_required: [test_rejects_permission_escalation]
  shutdown_condition: policy corruption
  human_review_required: true
""".strip(),
        encoding="utf-8",
    )

    assert load_card(path).name == "nucleus"


def test_load_registry_finds_all_yaml_files(tmp_path: Path):
    organelles = tmp_path / "organelles"
    organelles.mkdir()
    (organelles / "nucleus.yaml").write_text(
        """
bio_component:
  name: nucleus
  scale: organelle
  biological_role: Houses genome and coordinates control.
  software_role: Governance kernel.
  implementation_status: planned
  inputs: [cell_state]
  outputs: [policy_decision]
  internal_state:
    identity: cell identity
  sensors: [health_score]
  control_rules: [reject unauthorized actions]
  repair_rules: [quarantine invalid policy state]
  recycle_rules: [forward stale data to lysosome]
  replication_rules: [require checkpoint pass]
  failure_modes: [permission escalation]
  safety_limits:
    production_access: false
  tests_required: [test_rejects_permission_escalation]
  shutdown_condition: policy corruption
  human_review_required: true
""".strip(),
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert [card.name for card in registry] == ["nucleus"]
