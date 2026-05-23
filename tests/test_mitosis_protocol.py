from bioscaffold.cell import BioCell
from bioscaffold.reproduction import ReproductionController
from bioscaffold.types import CellRole, LifecyclePhase


def test_mitosis_requires_g2_phase():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    controller = ReproductionController()

    result = controller.mitosis(parent)

    assert result.succeeded is False
    assert result.reason == "parent must be in G2 before mitosis"


def test_mitosis_creates_restricted_child_from_healthy_parent():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    parent.phase = LifecyclePhase.G2
    controller = ReproductionController()

    result = controller.mitosis(parent)

    assert result.succeeded is True
    assert result.child is not None
    assert result.child.identity.parent_ids == (parent.identity.cell_id,)
    assert result.child.identity.permission_profile == "sandbox_child"
    assert result.child.active is True


def test_mitosis_allows_one_child_per_parent_cycle():
    parent = BioCell.bootstrap(role=CellRole.WORKER)
    parent.phase = LifecyclePhase.G2
    controller = ReproductionController()

    first = controller.mitosis(parent)
    second = controller.mitosis(parent)

    assert first.succeeded is True
    assert second.succeeded is False
    assert second.reason == "max children per cycle reached"
