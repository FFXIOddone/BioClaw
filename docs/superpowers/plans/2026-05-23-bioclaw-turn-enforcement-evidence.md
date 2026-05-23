# BioClaw Turn Enforcement Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each BioClaw turn close only after authorized, terminal, inspectable microtasks have produced reviewable evidence for the next generation.

**Architecture:** Turn closure becomes the first hard safety gate by enforcing `AgentHatPolicy` and deriving next-turn proposals from blocked, failed, and quarantined terminal tasks. Expression emits blocked/failed tasks instead of raising raw registry errors. Generation review and growth-cycle execution reject ghost refs and route all completed molecular outputs through immune inspection before promotion.

**Tech Stack:** Python 3.13, dataclasses, pytest, local `bioscaffold` package.

---

## File Structure

- `bioscaffold/turns.py`: add structured `TurnProposal`, enforce hat policy in `TurnEngine.close()`, preserve derived next-turn proposals.
- `bioscaffold/expression.py`: turn missing inputs and duplicate output refs into terminal task evidence.
- `bioscaffold/generations.py`: reject missing output refs and preserve quarantined refs as explicit review evidence.
- `bioscaffold/growth.py`: inspect normal completed outputs, not only injected pathogen fixtures.
- `bioscaffold/organism.py`: make reviewed generation integration idempotent for repeated review results.
- `bioscaffold/__init__.py`: export new public turn proposal type if added.
- `tests/test_turns.py`: cover policy enforcement and proposal derivation.
- `tests/test_expression.py`: cover missing input and repeat-cycle duplicate behavior.
- `tests/test_generations.py`: cover ghost output rejection.
- `tests/test_growth.py`: cover immune inspection of normal growth outputs.
- `tests/test_organism.py`: cover duplicate generation integration.

---

### Task 1: Turn Hat Enforcement And Proposals

**Files:**
- Modify: `bioscaffold/turns.py`
- Modify: `bioscaffold/__init__.py`
- Test: `tests/test_turns.py`

- [ ] **Step 1: Write failing tests**

Add tests that show `TurnEngine.close()` denies an unauthorized terminal task and derives next-turn proposals from non-success terminal tasks:

```python
def test_turn_rejects_unauthorized_hat_operation():
    task = MicroTask(
        task_id="task.bad.inject",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        scale=BioScale.MOLECULAR,
        operation=MicroOperation.INJECT,
        target_ref="plasmid.bad",
        agent_hat=AgentHat.GENE_SCOUT,
    ).with_terminal(TaskState.COMPLETE, reason="bad injection", outputs=("plasmid.bad",))

    with pytest.raises(ValueError, match="hat gene_scout cannot perform inject"):
        TurnEngine().close(
            Turn(
                turn_id="turn_000001",
                generation_id="gen_000001",
                organism_id="organism_000001",
                tasks=(task,),
            )
        )


def test_turn_derives_next_turn_proposals_from_failed_blocked_and_quarantined_tasks():
    turn = Turn(
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
        tasks=(
            make_task("task_failed", TaskState.FAILED),
            make_task("task_blocked", TaskState.BLOCKED),
            make_task("task_quarantined", TaskState.QUARANTINED),
        ),
    )

    closed = TurnEngine().close(turn)

    assert [proposal.source_task_id for proposal in closed.next_turn_proposals] == [
        "task_failed",
        "task_blocked",
        "task_quarantined",
    ]
    assert [proposal.recommended_operation for proposal in closed.next_turn_proposals] == [
        MicroOperation.VALIDATE,
        MicroOperation.FIND,
        MicroOperation.NEUTRALIZE,
    ]
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_turns.py -v`

Expected: FAIL because unauthorized tasks are currently accepted and `next_turn_proposals` is currently a tuple of strings.

- [ ] **Step 3: Implement minimal turn enforcement**

Add a frozen `TurnProposal` dataclass in `turns.py`, change `next_turn_proposals` to `tuple[TurnProposal, ...]`, and update `TurnEngine.close()` to use `AgentHatPolicy.default()` unless a policy is supplied. For each terminal task with `FAILED`, `BLOCKED`, or `QUARANTINED`, create a proposal with the source task, target ref, source state, recommended operation, recommended hat, and reason.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_turns.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/turns.py bioscaffold/__init__.py tests/test_turns.py
git commit -m "Enforce turn hat policy and proposals"
```

---

### Task 2: Expression Terminal Error Evidence

**Files:**
- Modify: `bioscaffold/expression.py`
- Test: `tests/test_expression.py`

- [ ] **Step 1: Write failing tests**

Add tests showing missing molecular inputs become blocked tasks and duplicate output refs become failed tasks:

```python
def test_expression_blocks_missing_gene_input():
    task = ExpressionEngine().transcribe(
        MoleculeRegistry(),
        gene_ref="gene.missing",
        promoter_ref="promoter.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.BLOCKED
    assert task.reason == "missing molecular input: gene.missing"


def test_expression_fails_duplicate_transcript_ref_instead_of_crashing():
    registry = seed_gene_and_promoter()
    engine = ExpressionEngine()
    first = engine.transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    second = engine.transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000002",
        generation_id="gen_000002",
        organism_id="organism_000001",
    )

    assert first.state is TaskState.COMPLETE
    assert second.state is TaskState.FAILED
    assert second.reason == "duplicate molecular output: transcript.auth.password_policy.v1"
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_expression.py -v`

Expected: FAIL because missing refs and duplicate refs currently raise exceptions.

- [ ] **Step 3: Implement minimal expression guards**

Wrap `registry.get()` calls with a helper that returns blocked task evidence for missing refs. Wrap `registry.add()` calls with a helper that returns failed task evidence for duplicate refs. Keep current deterministic ref names for this slice so repeat collisions are visible evidence.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_expression.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/expression.py tests/test_expression.py
git commit -m "Convert expression registry errors to terminal evidence"
```

---

### Task 3: Generation And Growth Immune Safety

**Files:**
- Modify: `bioscaffold/generations.py`
- Modify: `bioscaffold/growth.py`
- Test: `tests/test_generations.py`
- Test: `tests/test_growth.py`

- [ ] **Step 1: Write failing tests**

Add tests showing missing refs do not promote and normal expression outputs with immune markers get quarantined:

```python
def test_generation_review_does_not_promote_missing_output_refs():
    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(terminal_task("task_ghost", TaskState.COMPLETE, "structure.missing"),),
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

    assert reviewed.promoted_structures == ()
```

```python
def test_growth_cycle_quarantines_normal_outputs_with_known_immune_markers():
    registry = seed_expression_registry()
    registry.add(
        MolecularStructure(
            ref="antibody.fake_completion_marker",
            molecule_type=MoleculeType.ANTIBODY,
            content="signature for fake done",
            markers=("fake_completion_marker",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="gene.poisoned",
            molecule_type=MoleculeType.GENE,
            content="Fake done output.",
            markers=("fake_completion_marker",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.poisoned",
            molecule_type=MoleculeType.PROMOTER,
            content="Activate poisoned work.",
            markers=("active",),
        )
    )
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    result = GrowthCycleRunner().run_generation(
        registry=registry,
        organism=organism,
        gene_ref="gene.poisoned",
        promoter_ref="promoter.poisoned",
        generation_id="gen_000001",
        turn_id="turn_000001",
        immune_system=ImmuneSystem(known_markers={"fake_completion_marker"}),
    )

    assert "transcript.poisoned.v1" in result.generation.quarantined_structures
    assert "transcript.poisoned.v1" not in result.generation.promoted_structures
    assert result.organism.status is OrganismStatus.QUARANTINED
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_generations.py tests/test_growth.py -v`

Expected: FAIL because missing refs currently promote and only injected fixtures are inspected.

- [ ] **Step 3: Implement generation and growth safety**

Change `_is_promotable()` to return `False` for missing refs. In `GrowthCycleRunner.run_generation()`, after expression tasks and fixture inspections, inspect every completed task output that exists in the registry and has not already been inspected. Append immune tasks and events for detections, so generation review sees quarantine tasks before promotion.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_generations.py tests/test_growth.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/generations.py bioscaffold/growth.py tests/test_generations.py tests/test_growth.py
git commit -m "Inspect growth outputs before generation promotion"
```

---

### Task 4: Organism Integration Idempotency

**Files:**
- Modify: `bioscaffold/organism.py`
- Test: `tests/test_organism.py`

- [ ] **Step 1: Write failing test**

Add a test that integrating the same reviewed generation twice does not duplicate generation history:

```python
def test_product_organism_integration_is_idempotent_for_same_generation():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    once = organism.integrate_generation(reviewed_generation())
    twice = once.integrate_generation(reviewed_generation())

    assert twice.generation_ids == ("gen_000001",)
    assert twice.stable_structures == ("protein.auth.password_policy.v1",)
```

- [ ] **Step 2: Run test to verify red**

Run: `python -m pytest tests/test_organism.py -v`

Expected: FAIL because `generation_ids` currently duplicates the same generation id.

- [ ] **Step 3: Implement idempotent generation history**

In `ProductOrganism.integrate_generation()`, build `generation_ids` with `dict.fromkeys((*self.generation_ids, generation.generation_id))` just like structures are already deduped.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_organism.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bioscaffold/organism.py tests/test_organism.py
git commit -m "Make organism generation integration idempotent"
```

---

## Final Verification

- [ ] Run `python -m pytest -v`
- [ ] Run `git diff --check`
- [ ] Review `git status --short --branch`
- [ ] Push `main` to `origin/main` after all checks pass.

## Self-Review

Spec coverage: this plan advances the turn/generation scaffold by enforcing terminal state, hat roles, immune challenge, next-turn proposals, and stable organism state. Placeholder scan: no placeholder tasks remain. Type consistency: `TurnProposal`, `MicroOperation`, `AgentHat`, and `TaskState` names match existing package types.
