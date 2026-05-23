from __future__ import annotations

from bioscaffold.types import RecycleReceipt


class Lysosome:
    def __init__(self, *, destructive_delete: bool = False) -> None:
        self._destructive_delete = destructive_delete
        self._archives: list[tuple[str, str, dict[str, object]]] = []

    @property
    def archives(self) -> tuple[tuple[str, str, dict[str, object]], ...]:
        return tuple(self._archives)

    def collect(self, item_type: str, metadata: dict[str, object]) -> RecycleReceipt:
        archive_ref = f"archive_{len(self._archives) + 1:06d}"
        archive_record = (archive_ref, item_type, dict(metadata))
        self._archives.append(archive_record)
        return RecycleReceipt(archive_ref=archive_ref, item_type=item_type, metadata=dict(metadata))

    def reclaim(self) -> dict[str, object]:
        return {
            "reclaimed_count": len(self._archives),
            "destructive_delete": self._destructive_delete,
        }
