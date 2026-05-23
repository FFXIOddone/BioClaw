# BioClaw Terminal Product Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the end-to-end BioClaw workflow that starts one product organism, grows it through gene-driven turns and generations, then reaches a terminal delivered/archive or failure state.

**Architecture:** Keep the microscopic engines as the source of truth. A new workflow runner orchestrates `GrowthCycleRunner` over a list of simple gene plans, reads generation evidence, and stops only at a terminal state. Generation review records blocked/failed evidence, organism integration turns that evidence into lifecycle state, and an active-organism registry enforces the one-product standard.

**Tech Stack:** Python 3.12, dataclasses, pytest, existing `bioscaffold` package.

---

## File Structure

- `bioscaffold/generations.py`: add blocked/failed task evidence and next-generation proposals to reviewed generations.
- `bioscaffold/organism.py`: add blocked/failed organism lifecycle states and delivery guards.
- `bioscaffold/workflow.py`: create product workflow plans, terminal result type, active organism registry, and terminal workflow runner.
- `bioscaffold/__init__.py`: export workflow public types.
- `bio_components/processes/product-workflow.yaml`: document the orchestration component.
- `tests/test_generations.py`: verify generation review records blocker/failure evidence.
- `tests/test_organism.py`: verify blocked/failed organisms cannot deliver.
- `tests/test_workflow.py`: verify archive, quarantine, failed, and single-active-product workflow behavior.
- `tests/test_component_cards.py`: update public API and component registry expectations.

---

### Task 1: Generation Evidence Completeness

**Files:**
- Modify: `bioscaffold/generations.py`
- Test: `tests/test_generations.py`

- [ ] **Step 1: Write failing generation evidence test**

```python
def test_generation_review_records_blocked_failed_and_next_generation_proposals():
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(
                terminal_task("task_blocked", TaskState.BLOCKED, "gene.blocked"),
                terminal_task("task_failed", TaskState.FAILED, "gene.failed"),
            ),
        )
    )

    reviewed = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        MoleculeRegistry(),
    )

    assert reviewed.blocked_tasks == ("task_blocked",)
    assert reviewed.failed_tasks == ("task_failed",)
    assert [proposal.source_task_id for proposal in reviewed.next_generation_proposals] == [
        "task_blocked",
        "task_failed",
    ]
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_generations.py::test_generation_review_records_blocked_failed_and_next_generation_proposals -v`

Expected: FAIL because `Generation` does not yet expose blocked, failed, or next-generation proposal evidence.

- [ ] **Step 3: Implement reviewed evidence fields**

Add frozen dataclass fields `blocked_tasks`, `failed_tasks`, and `next_generation_proposals` to `Generation`. In `GenerationEngine.review()`, collect blocked/failed task ids and copy `Turn.next_turn_proposals` into generation-level proposal evidence.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_generations.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/generations.py tests/test_generations.py
git commit -m "Record generation blocker evidence"
```

---

### Task 2: Organism Failure Lifecycle

**Files:**
- Modify: `bioscaffold/organism.py`
- Test: `tests/test_organism.py`

- [ ] **Step 1: Write failing organism lifecycle tests**

```python
def test_product_organism_becomes_blocked_from_blocked_generation():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    blocked = organism.integrate_generation(
        reviewed_generation(promoted=(), blocked=("task_blocked",))
    )

    assert blocked.status is OrganismStatus.BLOCKED
    with pytest.raises(ValueError, match="blocked organism cannot be delivered"):
        blocked.deliver()


def test_product_organism_becomes_failed_from_failed_generation():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    failed = organism.integrate_generation(
        reviewed_generation(promoted=(), failed=("task_failed",))
    )

    assert failed.status is OrganismStatus.FAILED
    with pytest.raises(ValueError, match="failed organism cannot be delivered"):
        failed.deliver()
```

- [ ] **Step 2: Run red tests**

Run: `python -m pytest tests/test_organism.py -v`

Expected: FAIL because blocked/failed organism states do not exist yet.

- [ ] **Step 3: Implement lifecycle failure states**

Add `BLOCKED` and `FAILED` to `OrganismStatus`. Update `ProductOrganism.integrate_generation()` to set `QUARANTINED`, `BLOCKED`, or `FAILED` before `GROWING`. Update `deliver()` to refuse blocked and failed organisms with explicit messages.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_organism.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/organism.py tests/test_organism.py
git commit -m "Add organism failure lifecycle states"
```

---

### Task 3: Terminal Product Workflow Runner

**Files:**
- Create: `bioscaffold/workflow.py`
- Modify: `bioscaffold/__init__.py`
- Test: `tests/test_workflow.py`
- Test: `tests/test_component_cards.py`

- [ ] **Step 1: Write failing workflow tests**

```python
def test_product_workflow_runs_clean_product_to_archived_terminal_state():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.auth.password_policy", "promoter.auth.password_policy"),),
        ),
    )

    assert result.terminal_state is WorkflowTerminalState.ARCHIVED
    assert result.organism.status is OrganismStatus.ARCHIVED
    assert result.organism.archive_ref == "archive.organism_000001.000001"
    assert "protein.auth.password_policy.v1" in result.organism.delivered_outputs
    assert [turn.status for turn in result.turns] == [TurnStatus.CLOSED]


def test_product_workflow_stops_quarantined_before_delivery():
    result = ProductWorkflowRunner().run_to_terminal(
        registry=seed_registry_with_poisoned_gene(),
        plan=ProductWorkflowPlan(
            organism_id="organism_000001",
            product_name="Authentication Module",
            genes=(WorkflowGenePlan("gene.poisoned", "promoter.poisoned"),),
        ),
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
    )

    assert result.terminal_state is WorkflowTerminalState.QUARANTINED
    assert result.organism.status is OrganismStatus.QUARANTINED
    assert result.organism.archive_ref == ""
```

- [ ] **Step 2: Run red tests**

Run: `python -m pytest tests/test_workflow.py -v`

Expected: FAIL because `bioscaffold.workflow` does not exist.

- [ ] **Step 3: Implement workflow runner**

Create immutable dataclasses `WorkflowGenePlan`, `ProductWorkflowPlan`, `ProductWorkflowResult`, enum `WorkflowTerminalState`, `ActiveOrganismRegistry`, and `ProductWorkflowRunner.run_to_terminal()`. The runner births a product, begins it in the active registry, runs each gene through `GrowthCycleRunner`, stops on `QUARANTINED`, `BLOCKED`, or `FAILED`, and otherwise delivers then archives the organism.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_workflow.py tests/test_component_cards.py::test_package_imports -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/workflow.py bioscaffold/__init__.py tests/test_workflow.py tests/test_component_cards.py
git commit -m "Add terminal product workflow runner"
```

---

### Task 4: Workflow Component Card

**Files:**
- Create: `bio_components/processes/product-workflow.yaml`
- Modify: `tests/test_component_cards.py`

- [ ] **Step 1: Write failing registry expectation**

Add `"product-workflow"` to the expected card names in `tests/test_component_cards.py`.

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_component_cards.py::test_all_repository_cards_are_valid -v`

Expected: FAIL until the new card exists.

- [ ] **Step 3: Add component card**

Create `bio_components/processes/product-workflow.yaml` describing the safe one-product birth-growth-deliver-archive workflow, with safety limits for no autonomous deployment and no multiple active organisms.

- [ ] **Step 4: Run focused card tests**

Run: `python -m pytest tests/test_component_cards.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bio_components/processes/product-workflow.yaml tests/test_component_cards.py
git commit -m "Add product workflow component card"
```

---

## Final Verification

- [ ] Run `python -m pytest -v`
- [ ] Run `git diff --check`
- [ ] Run `git status --short --branch`
- [ ] Push `main` to `origin/main`.

## Self-Review

Spec coverage: this plan completes the macroscopic workflow requirement by connecting one active organism, microscopic gene plans, turn/generation barriers, immune hardening, delivery, and archive/death. Placeholder scan: no placeholders remain. Type consistency: workflow types use existing `ProductOrganism`, `GrowthCycleRunner`, `Generation`, `Turn`, `ImmuneSystem`, and `PathogenFixture` contracts.
