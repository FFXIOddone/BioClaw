from __future__ import annotations

from bioscaffold.types import LifecyclePhase, PolicyDecision


class LifecyclePolicy:
    def __init__(self) -> None:
        self._allowed = {
            (LifecyclePhase.G0, LifecyclePhase.G1),
            (LifecyclePhase.G1, LifecyclePhase.S),
            (LifecyclePhase.S, LifecyclePhase.G2),
            (LifecyclePhase.G2, LifecyclePhase.M),
            (LifecyclePhase.M, LifecyclePhase.CYTOKINESIS),
            (LifecyclePhase.CYTOKINESIS, LifecyclePhase.G0),
            (LifecyclePhase.G0, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G1, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.S, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G2, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.M, LifecyclePhase.APOPTOTIC),
            (LifecyclePhase.G0, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.G1, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.S, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.G2, LifecyclePhase.QUARANTINED),
            (LifecyclePhase.M, LifecyclePhase.QUARANTINED),
        }

    def can_transition(self, current: LifecyclePhase, target: LifecyclePhase) -> PolicyDecision:
        if (current, target) in self._allowed:
            return PolicyDecision.allow(f"transition {current.value}->{target.value} allowed")
        return PolicyDecision.deny(f"transition {current.value}->{target.value} is not allowed")
