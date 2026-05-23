from __future__ import annotations

from bioscaffold.types import CellIdentity, CellRole, LifecyclePhase, PolicyDecision


class Nucleus:
    def __init__(self, *, allowed_actions: set[str], permission_profile: str) -> None:
        self._allowed_actions = set(allowed_actions)
        self._permission_profile = permission_profile
        self._cell_counter = 0
        self._phase = LifecyclePhase.G0

    @property
    def phase(self) -> LifecyclePhase:
        return self._phase

    def authorize(self, action: str) -> PolicyDecision:
        if action not in self._allowed_actions:
            return PolicyDecision.deny(f"action {action} is not allowed")
        return PolicyDecision.allow()

    def assign_identity(
        self,
        *,
        genome_hash: str,
        snapshot_id: str,
        role: CellRole,
    ) -> CellIdentity:
        self._cell_counter += 1
        return CellIdentity.root(
            cell_id=f"cell_{self._cell_counter:06d}",
            genome_hash=genome_hash,
            snapshot_id=snapshot_id,
            role=role,
            permission_profile=self._permission_profile,
        )

    def transition_phase(self, target_phase: LifecyclePhase) -> PolicyDecision:
        self._phase = target_phase
        return PolicyDecision.allow(f"phase changed to {target_phase.value}")
