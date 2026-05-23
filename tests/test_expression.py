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


def test_expression_blocks_missing_promoter_input():
    registry = MoleculeRegistry()
    registry.add(
        MolecularStructure(
            ref="gene.auth.password_policy",
            molecule_type=MoleculeType.GENE,
            content="Require password policy.",
        )
    )

    task = ExpressionEngine().transcribe(
        registry,
        gene_ref="gene.auth.password_policy",
        promoter_ref="promoter.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.BLOCKED
    assert task.reason == "missing molecular input: promoter.missing"


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


def test_expression_blocks_missing_transcript_input():
    task = ExpressionEngine().splice(
        MoleculeRegistry(),
        transcript_ref="transcript.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.BLOCKED
    assert task.reason == "missing molecular input: transcript.missing"


def test_expression_blocks_missing_spliced_input():
    task = ExpressionEngine().translate(
        MoleculeRegistry(),
        spliced_ref="spliced.missing",
        turn_id="turn_000001",
        generation_id="gen_000001",
        organism_id="organism_000001",
    )

    assert task.state is TaskState.BLOCKED
    assert task.reason == "missing molecular input: spliced.missing"


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
