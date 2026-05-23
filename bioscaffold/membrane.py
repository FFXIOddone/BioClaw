from __future__ import annotations

from bioscaffold.types import ValidationResult


class Membrane:
    def __init__(self, *, allowed_input_keys: set[str], allowed_output_keys: set[str]) -> None:
        self._allowed_input_keys = set(allowed_input_keys)
        self._allowed_output_keys = set(allowed_output_keys)

    def validate_input(self, payload: dict[str, object]) -> ValidationResult:
        unknown = sorted(set(payload).difference(self._allowed_input_keys))
        if unknown:
            return ValidationResult(False, f"unknown input keys: {', '.join(unknown)}")
        return ValidationResult(True)

    def validate_output(self, payload: dict[str, object]) -> ValidationResult:
        unknown = sorted(set(payload).difference(self._allowed_output_keys))
        if unknown:
            return ValidationResult(False, f"unknown output keys: {', '.join(unknown)}")
        return ValidationResult(True)
