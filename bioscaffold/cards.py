from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


Scale = Literal[
    "molecular",
    "protein_complex",
    "organelle",
    "cell",
    "tissue",
    "organ",
    "organism",
    "ecosystem",
]


class BioComponentCard(BaseModel):
    name: str
    scale: Scale
    biological_role: str
    software_role: str
    implementation_status: str = "planned"
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    internal_state: dict[str, str] = Field(min_length=1)
    sensors: list[str] = Field(min_length=1)
    control_rules: list[str] = Field(min_length=1)
    repair_rules: list[str] = Field(min_length=1)
    recycle_rules: list[str] = Field(min_length=1)
    replication_rules: list[str] = Field(min_length=1)
    failure_modes: list[str] = Field(min_length=1)
    safety_limits: dict[str, Any] = Field(min_length=1)
    tests_required: list[str] = Field(min_length=1)
    shutdown_condition: str
    human_review_required: bool

    @field_validator("name")
    @classmethod
    def name_must_be_kebab_or_lower_snake(cls, value: str) -> str:
        if value != value.lower():
            raise ValueError("name must be lowercase")
        if " " in value:
            raise ValueError("name must not contain spaces")
        return value


def load_card(path: Path) -> BioComponentCard:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "bio_component" not in raw:
        raise ValueError(f"{path} must contain a bio_component root object")
    return BioComponentCard.model_validate(raw["bio_component"])


def load_registry(root: Path) -> list[BioComponentCard]:
    cards = [load_card(path) for path in sorted(root.rglob("*.yaml"))]
    names = [card.name for card in cards]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate bio component cards: {', '.join(duplicates)}")
    return cards
