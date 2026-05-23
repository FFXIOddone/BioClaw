from __future__ import annotations

from bioscaffold.types import BudgetReport, BudgetRequest, BudgetReservation


class Mitochondria:
    def __init__(
        self,
        *,
        max_runtime_seconds: float,
        max_memory_mb: float,
        max_tokens: int = 0,
        max_api_cost_usd: float = 0.0,
    ) -> None:
        self._runtime_seconds_remaining = max_runtime_seconds
        self._memory_mb_remaining = max_memory_mb
        self._tokens_remaining = max_tokens
        self._api_cost_usd_remaining = max_api_cost_usd
        self._reservation_count = 0

    def reserve(self, request: BudgetRequest) -> BudgetReservation:
        self._reservation_count += 1
        reservation_id = f"budget_{self._reservation_count:06d}"
        if request.runtime_seconds > self._runtime_seconds_remaining:
            return BudgetReservation(reservation_id, request, False, "runtime budget exceeded")
        if request.memory_mb > self._memory_mb_remaining:
            return BudgetReservation(reservation_id, request, False, "memory budget exceeded")
        if request.tokens > self._tokens_remaining:
            return BudgetReservation(reservation_id, request, False, "token budget exceeded")
        if request.api_cost_usd > self._api_cost_usd_remaining:
            return BudgetReservation(reservation_id, request, False, "api cost budget exceeded")

        self._runtime_seconds_remaining -= request.runtime_seconds
        self._memory_mb_remaining -= request.memory_mb
        self._tokens_remaining -= request.tokens
        self._api_cost_usd_remaining -= request.api_cost_usd
        return BudgetReservation(reservation_id, request, True, "reserved")

    def report(self) -> BudgetReport:
        return BudgetReport(
            runtime_seconds_remaining=self._runtime_seconds_remaining,
            memory_mb_remaining=self._memory_mb_remaining,
            tokens_remaining=self._tokens_remaining,
            api_cost_usd_remaining=self._api_cost_usd_remaining,
        )
