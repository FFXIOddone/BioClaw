# BioClaw All-Generation Product Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the product workflow generation by connecting genome compilation, executable proposals, validation, assembly, hardening evidence, delivery reporting, and a runner API around project microtasks.

**Architecture:** Keep existing microtask, turn, generation, growth, and workflow primitives. Add small focused modules that sit above them: a genome compiler converts product requirements into DNA/gene/promoter structures; a proposal planner materializes generation proposals into project microtasks; validation and assembly engines create project evidence after growth; a delivery packager emits the archive report; an all-generation runner coordinates the full product request to terminal state.

**Tech Stack:** Python 3.12, dataclasses, pytest, existing `bioscaffold` package.

---

## File Structure

- `bioscaffold/compiler.py`: compile product requirements into DNA, genes, promoters, and `ProductWorkflowPlan`.
- `bioscaffold/proposals.py`: convert `Generation.next_generation_proposals` into terminal project microtasks.
- `bioscaffold/validation.py`: validate protein artifact fragments and create antibody memory for invalid markers.
- `bioscaffold/assembly.py`: promote validated protein artifacts into module/subsystem/capability structures.
- `bioscaffold/delivery.py`: create a delivery report from terminal workflow evidence.
- `bioscaffold/all_generation.py`: coordinate the full product request through compiler, workflow runner, proposals, validation, assembly, and delivery report.
- `bioscaffold/molecules.py`: add molecule types for module, subsystem, capability, and delivery package.
- `bioscaffold/expression.py`: preserve transcript markers on protein artifacts so validation and hardening can reason over lineage.
- `bioscaffold/__init__.py`: export public all-generation workflow types.
- `tests/test_all_generation_workflow.py`: cover the complete product request path and focused engines.
- `tests/test_component_cards.py`: update public API expectations.

---

## One-Generation Tasks

- [ ] Write failing tests for genome compilation, proposal materialization, validation memory, and full all-generation runner.
- [ ] Implement the focused modules and exports.
- [ ] Run focused tests until green.
- [ ] Run full verification.
- [ ] Commit and push the completed generation.

## Acceptance Criteria

- A product request can compile into DNA, genes, promoters, and a runnable product workflow plan.
- Product workflow output includes runtime project microtasks, not Codex implementation tasks.
- Generation proposals become executable project microtasks.
- Protein artifacts validate with terminal evidence.
- Invalid markers create antibody memory.
- Validated artifacts assemble upward into module, subsystem, and capability structures.
- Archived terminal workflows emit a delivery report with lineage, tasks, generations, immune events, assembly refs, and archive ref.
- The whole slice completes in one generation with tests passing.
