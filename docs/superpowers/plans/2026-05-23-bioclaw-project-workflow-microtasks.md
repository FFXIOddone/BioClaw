# BioClaw Project Workflow Microtasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the runtime product workflow emit project microtasks, so BioClaw models the product's own work instead of Codex's implementation workflow.

**Architecture:** Product workflow planning creates `MicroTask` records for project operations: birth, find gene, find promoter, expression, immune inspection, delivery, archive, and terminal failure evidence. The gene-discovery tasks run inside the same growth turn as expression by passing prefix tasks into `GrowthCycleRunner`. The workflow result exposes a flattened `project_microtasks` tuple for birth-to-death audit.

**Tech Stack:** Python 3.12, dataclasses, pytest, existing `bioscaffold` package.

---

## File Structure

- `bioscaffold/growth.py`: accept terminal project prefix tasks and skip expression if they block/fail.
- `bioscaffold/workflow.py`: add `ProjectWorkflowMicroTaskFactory`, record project lifecycle tasks, and expose `project_microtasks` on `ProductWorkflowResult`.
- `bioscaffold/__init__.py`: export `ProjectWorkflowMicroTaskFactory`.
- `tests/test_growth.py`: verify prefix tasks are inside the same generation turn and can block expression.
- `tests/test_workflow.py`: verify result microtasks describe project workflow operations only.
- `tests/test_component_cards.py`: update public API expectations.

---

### Task 1: Growth Prefix Project Tasks

**Files:**
- Modify: `bioscaffold/growth.py`
- Test: `tests/test_growth.py`

- [ ] **Step 1: Write failing tests**

Add tests proving a terminal project prefix task is included in the same closed turn and that blocked prefix tasks stop expression:

```python
def test_growth_cycle_includes_project_prefix_tasks_in_same_turn():
    prefix = MicroTask(
        task_id="task.workflow.find_gene.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.auth.password_policy",
        agent_hat=AgentHat.GENE_SCOUT,
        expected_output="gene_ref",
    ).with_terminal(TaskState.COMPLETE, reason="project gene located", outputs=("gene.auth.password_policy",))

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=ProductOrganism.birth(
            organism_id="organism_000001",
            product_name="Authentication Module",
        ),
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
        prefix_tasks=(prefix,),
    )

    assert result.turn.tasks[0] == prefix
    assert "protein.auth.password_policy.v1" in result.generation.promoted_structures


def test_growth_cycle_prefix_blocker_stops_expression():
    prefix = MicroTask(
        task_id="task.workflow.find_gene.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.FIND,
        target_ref="gene.missing",
        agent_hat=AgentHat.GENE_SCOUT,
        expected_output="gene_ref",
    ).with_terminal(TaskState.BLOCKED, reason="missing project gene")

    result = GrowthCycleRunner().run_generation(
        registry=seed_expression_registry(),
        organism=ProductOrganism.birth(
            organism_id="organism_000001",
            product_name="Authentication Module",
        ),
        gene_ref="gene.missing",
        promoter_ref="promoter.auth.password_policy",
        generation_id="gen_000001",
        turn_id="turn_000001",
        prefix_tasks=(prefix,),
    )

    assert result.turn.tasks == (prefix,)
    assert result.generation.blocked_tasks == ("task.workflow.find_gene.missing",)
    assert result.organism.status is OrganismStatus.BLOCKED
```

- [ ] **Step 2: Run red tests**

Run: `python -m pytest tests/test_growth.py -v`

Expected: FAIL because `GrowthCycleRunner.run_generation()` does not accept `prefix_tasks`.

- [ ] **Step 3: Implement prefix tasks**

Add `prefix_tasks: tuple[MicroTask, ...] = ()` to `run_generation()`, seed `tasks` with those tasks, and skip expression unless every prefix task is `TaskState.COMPLETE`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_growth.py -v`

Expected: PASS.

---

### Task 2: Project Workflow Microtask Result

**Files:**
- Modify: `bioscaffold/workflow.py`
- Modify: `bioscaffold/__init__.py`
- Test: `tests/test_workflow.py`
- Test: `tests/test_component_cards.py`

- [ ] **Step 1: Write failing workflow tests**

Add tests showing product workflow project microtasks include birth, find, expression, delivery, and archive, and that missing genes block inside project microtask evidence.

- [ ] **Step 2: Run red tests**

Run: `python -m pytest tests/test_workflow.py tests/test_component_cards.py::test_package_imports -v`

Expected: FAIL because `project_microtasks` and `ProjectWorkflowMicroTaskFactory` do not exist.

- [ ] **Step 3: Implement project microtask factory**

Create `ProjectWorkflowMicroTaskFactory` in `workflow.py`. It must create terminal `MicroTask` records for birth, gene discovery, promoter discovery, delivery, archive, and terminal blocked/failed/quarantined evidence. `ProductWorkflowRunner` must add discovery tasks as growth prefix tasks and return all product microtasks in `ProductWorkflowResult.project_microtasks`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_workflow.py tests/test_component_cards.py::test_package_imports -v`

Expected: PASS.

---

## Final Verification

- [ ] Run `python -m pytest -v`
- [ ] Run `git diff --check`
- [ ] Commit all changes as one generation.
- [ ] Push `main` to `origin/main`.

## Self-Review

Spec coverage: this plan makes runtime product workflow tasks microscopic and auditable, without modeling Codex's implementation workflow. Placeholder scan: no placeholders remain. Type consistency: all new runtime tasks use existing `MicroTask`, `MicroOperation`, `AgentHat`, `TaskState`, `Turn`, `Generation`, and `ProductWorkflowResult` contracts.
