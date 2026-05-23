# BioClaw Expression Organism Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable path from product genes to artifact fragments and from reviewed growth to product delivery/archive.

**Architecture:** Keep the existing primitive modules intact. Add `expression.py` for DNA/RNA-level expression operations and `organism.py` for the single active product organism lifecycle. Use the existing `MicroTask`, `Turn`, `Generation`, `MoleculeRegistry`, and immune primitives rather than creating a separate workflow runtime.

**Tech Stack:** Python 3.12, dataclasses, enums, pytest, existing BioComponent YAML registry.

---

## File Structure

- Create `bioscaffold/expression.py`: `ExpressionEngine` for transcribe, splice, and translate operations.
- Create `bioscaffold/organism.py`: `ProductOrganism` and `OrganismStatus` for birth, growth integration, delivery, and archive.
- Create `tests/test_expression.py`: expression operation tests and a gene-to-protein turn/generation test.
- Create `tests/test_organism.py`: product lifecycle tests.
- Modify `tests/test_component_cards.py`: add cards and public exports to expectations.
- Modify `bioscaffold/__init__.py`: export expression and organism lifecycle primitives.
- Create `bio_components/processes/translation.yaml`: card for transcript-to-artifact translation.
- Create `bio_components/organism/product-organism.yaml`: card for product organism lifecycle.

## Task 1: Translation And Product Organism Cards

**Files:**
- Modify: `tests/test_component_cards.py`
- Create: `bio_components/organism/product-organism.yaml`
- Create: `bio_components/processes/translation.yaml`

- [x] **Step 1: Write the failing registry expectation**

Add `"product-organism"` and `"translation"` to the expected card-name set in `tests/test_component_cards.py`.

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_component_cards.py::test_all_repository_cards_are_valid -v`

Expected: FAIL because `product-organism` and `translation` are missing.

- [x] **Step 3: Add cards**

Create `bio_components/organism/product-organism.yaml`:

```yaml
bio_component:
  name: product-organism
  scale: organism
  biological_role: Represents the whole living system across birth, growth, and death.
  software_role: Represents one active product from build start through delivery and archive.
  implementation_status: planned
  inputs: [reviewed_generation]
  outputs: [delivered_product, archive_ref]
  internal_state:
    status: Planned, born, growing, delivered, archived, or quarantined.
  sensors: [generation_count, stable_structure_count, quarantine_count]
  control_rules: [Only reviewed generations can change organism growth state.]
  repair_rules: [Quarantined growth blocks delivery until reviewed.]
  recycle_rules: [Delivered products are archived before leaving active flow.]
  replication_rules: [Only one active product organism is standard.]
  failure_modes: [delivery with quarantined structures, archive before delivery]
  safety_limits:
    autonomous_deployment: false
    multiple_active_organisms: false
  tests_required: [test_product_organism_delivers_and_archives_reviewed_growth]
  shutdown_condition: Product lifecycle state becomes contradictory.
  human_review_required: true
```

Create `bio_components/processes/translation.yaml`:

```yaml
bio_component:
  name: translation
  scale: molecular
  biological_role: Converts RNA instructions into protein products.
  software_role: Converts spliced transcripts into artifact fragments.
  implementation_status: planned
  inputs: [spliced_transcript]
  outputs: [protein_artifact]
  internal_state:
    source_transcript_ref: Spliced transcript being translated.
  sensors: [translation_status]
  control_rules: [Only spliced transcripts can be translated.]
  repair_rules: [Invalid transcripts become failed tasks with evidence.]
  recycle_rules: [Failed artifact fragments are archived.]
  replication_rules: [Protein artifacts preserve transcript lineage.]
  failure_modes: [unspliced transcript, missing lineage]
  safety_limits:
    direct_deployment: false
  tests_required: [test_expression_pipeline_closes_gene_to_artifact_turn]
  shutdown_condition: Artifact lineage cannot be traced to a transcript.
  human_review_required: true
```

- [x] **Step 4: Run card tests**

Run: `python -m pytest tests/test_component_cards.py tests/test_card_registry.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_component_cards.py bio_components/organism bio_components/processes/translation.yaml
git commit -m "Add product organism and translation cards"
```

## Task 2: Expression Engine

**Files:**
- Create: `tests/test_expression.py`
- Create: `bioscaffold/expression.py`

- [x] **Step 1: Write failing expression tests**

Create `tests/test_expression.py`:

```python
import pytest

from bioscaffold.expression import ExpressionEngine
from bioscaffold.generations import Generation, GenerationEngine, GenerationStatus
from bioscaffold.microtasks import TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType
from bioscaffold.turns import Turn, TurnEngine, TurnStatus


def seed_gene_and_promoter() -> MoleculeRegistry:
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
            source_refs=("dna.product_blueprint",),
            markers=("auth",),
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.auth.password_policy",
            molecule_type=MoleculeType.PROMOTER,
            content="Activate password policy work.",
            source_refs=("gene.auth.password_policy",),
            markers=("active",),
        )
    )
    return registry


def test_expression_transcribes_active_gene_to_rna():
    registry = seed_gene_and_promoter()

    task = ExpressionEngine().transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    transcript = registry.get("transcript.auth.password_policy.v1")
    assert task.state is TaskState.COMPLETE
    assert task.outputs == ("transcript.auth.password_policy.v1",)
    assert transcript.molecule_type is MoleculeType.RNA_TRANSCRIPT
    assert transcript.source_refs == ("gene.auth.password_policy", "promoter.auth.password_policy")


def test_expression_blocks_inactive_promoter():
    registry = seed_gene_and_promoter()
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
        )
    )
    registry.add(
        MolecularStructure(
            ref="promoter.auth.password_policy",
            molecule_type=MoleculeType.PROMOTER,
            content="Inactive password policy work.",
            markers=("inactive",),
        )
    )

    task = ExpressionEngine().transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.BLOCKED
    assert task.reason == "promoter promoter.auth.password_policy is not active"


def test_expression_splices_transcript_and_translates_artifact():
    registry = seed_gene_and_promoter()
    engine = ExpressionEngine()
    transcribe_task = engine.transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    splice_task = engine.splice(
        registry,
        transcript_ref=transcribe_task.outputs[0],
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    translate_task = engine.translate(
        registry,
        spliced_ref=splice_task.outputs[0],
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert splice_task.state is TaskState.COMPLETE
    assert translate_task.state is TaskState.COMPLETE
    assert registry.get("spliced.auth.password_policy.v1").molecule_type is MoleculeType.SPLICED_TRANSCRIPT
    assert registry.get("protein.auth.password_policy.v1").molecule_type is MoleculeType.PROTEIN


def test_expression_pipeline_closes_gene_to_artifact_turn():
    registry = seed_gene_and_promoter()
    engine = ExpressionEngine()
    transcribe_task = engine.transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.auth.password_policy",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    splice_task = engine.splice(
        registry,
        transcript_ref=transcribe_task.outputs[0],
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )
    translate_task = engine.translate(
        registry,
        spliced_ref=splice_task.outputs[0],
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    turn = TurnEngine().close(
        Turn(
            turn_id="turn_000001",
            generation_id="gen_000001",
            organism_id="organism_000001",
            tasks=(transcribe_task, splice_task, translate_task),
        )
    )
    generation = GenerationEngine().review(
        Generation(
            generation_id="gen_000001",
            organism_id="organism_000001",
            turns=(turn,),
        ),
        registry,
    )

    assert turn.status is TurnStatus.CLOSED
    assert generation.status is GenerationStatus.REVIEWED
    assert "protein.auth.password_policy.v1" in generation.promoted_structures
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_expression.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.expression'`.

- [x] **Step 3: Implement expression engine**

Create `bioscaffold/expression.py`:

```python
from __future__ import annotations

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


class ExpressionEngine:
    def transcribe(
        self,
        registry: MoleculeRegistry,
        *,
        gene_ref: str,
        promoter_ref: str,
        turn_id: str,
        generation_id: str,
        organism_id: str,
    ) -> MicroTask:
        task = MicroTask(
            task_id=f"task.transcribe.{self._suffix(gene_ref)}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.MOLECULAR,
            operation=MicroOperation.TRANSCRIBE,
            target_ref=gene_ref,
            agent_hat=AgentHat.TRANSCRIBER,
            inputs=(gene_ref, promoter_ref),
            expected_output="rna_transcript",
        )
        gene = registry.get(gene_ref)
        promoter = registry.get(promoter_ref)
        if gene.molecule_type is not MoleculeType.GENE:
            return task.with_terminal(TaskState.FAILED, reason=f"{gene_ref} is not a gene")
        if promoter.molecule_type is not MoleculeType.PROMOTER:
            return task.with_terminal(TaskState.FAILED, reason=f"{promoter_ref} is not a promoter")
        if "active" not in promoter.markers:
            return task.with_terminal(
                TaskState.BLOCKED,
                reason=f"promoter {promoter_ref} is not active",
            )

        transcript_ref = f"transcript.{self._suffix(gene_ref)}.v1"
        registry.add(
            MolecularStructure(
                ref=transcript_ref,
                molecule_type=MoleculeType.RNA_TRANSCRIPT,
                content=gene.content,
                source_refs=(gene_ref, promoter_ref),
                markers=tuple(dict.fromkeys((*gene.markers, "transcribed"))),
            )
        )
        return task.with_terminal(
            TaskState.COMPLETE,
            reason="gene transcribed",
            outputs=(transcript_ref,),
        )

    def splice(
        self,
        registry: MoleculeRegistry,
        *,
        transcript_ref: str,
        turn_id: str,
        generation_id: str,
        organism_id: str,
    ) -> MicroTask:
        task = MicroTask(
            task_id=f"task.splice.{self._suffix(transcript_ref)}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.MOLECULAR,
            operation=MicroOperation.SPLICE,
            target_ref=transcript_ref,
            agent_hat=AgentHat.SPLICER,
            inputs=(transcript_ref,),
            expected_output="spliced_transcript",
        )
        transcript = registry.get(transcript_ref)
        if transcript.molecule_type is not MoleculeType.RNA_TRANSCRIPT:
            return task.with_terminal(TaskState.FAILED, reason=f"{transcript_ref} is not an RNA transcript")
        if "malformed" in transcript.markers:
            return task.with_terminal(TaskState.QUARANTINED, reason="transcript is malformed")

        spliced_ref = f"spliced.{self._suffix(transcript_ref)}"
        registry.add(
            MolecularStructure(
                ref=spliced_ref,
                molecule_type=MoleculeType.SPLICED_TRANSCRIPT,
                content=transcript.content.replace("[inactive]", "").strip(),
                source_refs=(transcript_ref,),
                markers=tuple(
                    marker for marker in (*transcript.markers, "spliced") if marker != "inactive_clause"
                ),
            )
        )
        return task.with_terminal(
            TaskState.COMPLETE,
            reason="transcript spliced",
            outputs=(spliced_ref,),
        )

    def translate(
        self,
        registry: MoleculeRegistry,
        *,
        spliced_ref: str,
        turn_id: str,
        generation_id: str,
        organism_id: str,
    ) -> MicroTask:
        task = MicroTask(
            task_id=f"task.translate.{self._suffix(spliced_ref)}",
            turn_id=turn_id,
            generation_id=generation_id,
            organism_id=organism_id,
            scale=BioScale.PROTEIN,
            operation=MicroOperation.TRANSLATE,
            target_ref=spliced_ref,
            agent_hat=AgentHat.RIBOSOME_WORKER,
            inputs=(spliced_ref,),
            expected_output="protein_artifact",
        )
        transcript = registry.get(spliced_ref)
        if transcript.molecule_type is not MoleculeType.SPLICED_TRANSCRIPT:
            return task.with_terminal(TaskState.FAILED, reason=f"{spliced_ref} is not a spliced transcript")

        protein_ref = f"protein.{self._suffix(spliced_ref)}"
        registry.add(
            MolecularStructure(
                ref=protein_ref,
                molecule_type=MoleculeType.PROTEIN,
                content=f"artifact fragment: {transcript.content}",
                source_refs=(spliced_ref,),
                markers=("artifact_fragment",),
            )
        )
        return task.with_terminal(
            TaskState.COMPLETE,
            reason="spliced transcript translated",
            outputs=(protein_ref,),
        )

    def _suffix(self, ref: str) -> str:
        return ref.split(".", 1)[1] if "." in ref else ref
```

- [x] **Step 4: Run expression tests**

Run: `python -m pytest tests/test_expression.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_expression.py bioscaffold/expression.py
git commit -m "Add gene expression engine"
```

## Task 3: Product Organism Lifecycle

**Files:**
- Create: `tests/test_organism.py`
- Create: `bioscaffold/organism.py`

- [x] **Step 1: Write failing organism tests**

Create `tests/test_organism.py`:

```python
import pytest

from bioscaffold.generations import Generation, GenerationStatus
from bioscaffold.organism import OrganismStatus, ProductOrganism


def reviewed_generation(
    *,
    promoted: tuple[str, ...] = ("protein.auth.password_policy.v1",),
    quarantined: tuple[str, ...] = (),
) -> Generation:
    return Generation(
        generation_id="gen_000001",
        organism_id="organism_000001",
        status=GenerationStatus.REVIEWED,
        promoted_structures=promoted,
        quarantined_structures=quarantined,
    )


def test_product_organism_birth_records_product_start():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    assert organism.status is OrganismStatus.BORN
    assert organism.product_name == "Authentication Module"
    assert organism.generation_ids == ()


def test_product_organism_delivers_and_archives_reviewed_growth():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    grown = organism.integrate_generation(reviewed_generation())
    delivered = grown.deliver()
    archived = delivered.archive()

    assert grown.status is OrganismStatus.GROWING
    assert delivered.status is OrganismStatus.DELIVERED
    assert delivered.delivered_outputs == ("protein.auth.password_policy.v1",)
    assert archived.status is OrganismStatus.ARCHIVED
    assert archived.archive_ref == "archive.organism_000001.000001"


def test_product_organism_refuses_delivery_with_quarantined_growth():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    quarantined = organism.integrate_generation(
        reviewed_generation(
            promoted=(),
            quarantined=("plasmid.injected.fake_done.v1",),
        )
    )

    assert quarantined.status is OrganismStatus.QUARANTINED
    with pytest.raises(ValueError, match="quarantined organism cannot be delivered"):
        quarantined.deliver()


def test_product_organism_requires_reviewed_generation():
    organism = ProductOrganism.birth(
        organism_id="organism_000001",
        product_name="Authentication Module",
    )

    with pytest.raises(ValueError, match="only reviewed generations can be integrated"):
        organism.integrate_generation(
            Generation(generation_id="gen_000001", organism_id="organism_000001")
        )
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_organism.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bioscaffold.organism'`.

- [x] **Step 3: Implement product organism**

Create `bioscaffold/organism.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from bioscaffold.generations import Generation, GenerationStatus


class OrganismStatus(str, Enum):
    PLANNED = "planned"
    BORN = "born"
    GROWING = "growing"
    DELIVERED = "delivered"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class ProductOrganism:
    organism_id: str
    product_name: str
    status: OrganismStatus = OrganismStatus.PLANNED
    generation_ids: tuple[str, ...] = ()
    stable_structures: tuple[str, ...] = ()
    quarantined_structures: tuple[str, ...] = ()
    delivered_outputs: tuple[str, ...] = ()
    archive_ref: str = ""

    @classmethod
    def birth(cls, *, organism_id: str, product_name: str) -> "ProductOrganism":
        return cls(
            organism_id=organism_id,
            product_name=product_name,
            status=OrganismStatus.BORN,
        )

    def integrate_generation(self, generation: Generation) -> "ProductOrganism":
        if generation.status is not GenerationStatus.REVIEWED:
            raise ValueError("only reviewed generations can be integrated")
        if generation.organism_id != self.organism_id:
            raise ValueError("generation belongs to a different organism")
        generation_ids = (*self.generation_ids, generation.generation_id)
        stable = tuple(dict.fromkeys((*self.stable_structures, *generation.promoted_structures)))
        quarantined = tuple(
            dict.fromkeys((*self.quarantined_structures, *generation.quarantined_structures))
        )
        status = OrganismStatus.QUARANTINED if quarantined else OrganismStatus.GROWING
        return replace(
            self,
            status=status,
            generation_ids=generation_ids,
            stable_structures=stable,
            quarantined_structures=quarantined,
        )

    def deliver(self) -> "ProductOrganism":
        if self.status is OrganismStatus.QUARANTINED:
            raise ValueError("quarantined organism cannot be delivered")
        if not self.stable_structures:
            raise ValueError("organism has no stable structures to deliver")
        return replace(
            self,
            status=OrganismStatus.DELIVERED,
            delivered_outputs=self.stable_structures,
        )

    def archive(self) -> "ProductOrganism":
        if self.status is not OrganismStatus.DELIVERED:
            raise ValueError("only delivered organisms can be archived")
        return replace(
            self,
            status=OrganismStatus.ARCHIVED,
            archive_ref=f"archive.{self.organism_id}.{len(self.generation_ids):06d}",
        )
```

- [x] **Step 4: Run organism tests**

Run: `python -m pytest tests/test_organism.py -v`

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add tests/test_organism.py bioscaffold/organism.py
git commit -m "Add product organism lifecycle"
```

## Task 4: Public Exports And Full Verification

**Files:**
- Modify: `tests/test_component_cards.py`
- Modify: `bioscaffold/__init__.py`

- [x] **Step 1: Write failing public export expectation**

Add `"ExpressionEngine"`, `"OrganismStatus"`, and `"ProductOrganism"` to the `bioscaffold.__all__` expectation in `tests/test_component_cards.py`.

- [x] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_component_cards.py::test_package_imports -v`

Expected: FAIL because new exports are not present.

- [x] **Step 3: Update public exports**

Import and export `ExpressionEngine`, `OrganismStatus`, and `ProductOrganism` in `bioscaffold/__init__.py`.

- [x] **Step 4: Run full verification**

Run: `python -m pytest -v`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit code 0.

- [x] **Step 5: Commit**

```powershell
git add bioscaffold/__init__.py tests/test_component_cards.py
git commit -m "Export expression and organism lifecycle"
```

## Self-Review

Spec coverage:

- DNA/RNA product growth: Task 2 implements gene -> transcript -> spliced transcript -> protein artifact.
- Turn/generation composition: Task 2 includes a full turn close and generation review over expression tasks.
- Single active product organism: Task 3 implements one product organism id and rejects cross-organism generation integration.
- Birth/death product lifecycle: Task 3 implements birth, growth, delivery, and archive.
- Card-first discipline: Task 1 adds cards before implementation modules.

Placeholder scan:

- No placeholder text is left in required steps.
- Every code task includes failing test, expected failure, implementation, verification, and commit.

Type consistency:

- `ExpressionEngine`, `ProductOrganism`, `OrganismStatus`, `MolecularStructure`, `MoleculeRegistry`, and `Generation` are consistently named across tests and implementation snippets.
