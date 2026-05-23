from __future__ import annotations

import hashlib
import json

from bioscaffold.types import SnapshotRef, ValidationResult


class Genome:
    def __init__(self, config: dict[str, object]) -> None:
        self._config = dict(config)
        self._snapshot_count = 0

    @property
    def config(self) -> dict[str, object]:
        return dict(self._config)

    def validate(self) -> ValidationResult:
        required = {"genome_id", "version", "allowed_roles", "allowed_paths", "budgets"}
        missing = sorted(required.difference(self._config))
        if missing:
            return ValidationResult(False, f"missing genome keys: {', '.join(missing)}")
        return ValidationResult(True)

    def checksum(self) -> str:
        payload = json.dumps(self._config, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def snapshot(self) -> SnapshotRef:
        self._snapshot_count += 1
        return SnapshotRef(
            snapshot_id=f"snapshot_{self._snapshot_count:06d}",
            genome_hash=self.checksum(),
        )
