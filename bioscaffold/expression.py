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
        try:
            gene = registry.get(gene_ref)
        except KeyError:
            return self._missing_input(task, gene_ref)
        try:
            promoter = registry.get(promoter_ref)
        except KeyError:
            return self._missing_input(task, promoter_ref)
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
        duplicate = self._add_structure(
            registry,
            task,
            MolecularStructure(
                ref=transcript_ref,
                molecule_type=MoleculeType.RNA_TRANSCRIPT,
                content=gene.content,
                source_refs=(gene_ref, promoter_ref),
                markers=tuple(dict.fromkeys((*gene.markers, "transcribed"))),
            )
        )
        if duplicate is not None:
            return duplicate
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
        try:
            transcript = registry.get(transcript_ref)
        except KeyError:
            return self._missing_input(task, transcript_ref)
        if transcript.molecule_type is not MoleculeType.RNA_TRANSCRIPT:
            return task.with_terminal(TaskState.FAILED, reason=f"{transcript_ref} is not an RNA transcript")
        if "malformed" in transcript.markers:
            return task.with_terminal(TaskState.QUARANTINED, reason="transcript is malformed")

        spliced_ref = f"spliced.{self._suffix(transcript_ref)}"
        duplicate = self._add_structure(
            registry,
            task,
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
        if duplicate is not None:
            return duplicate
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
        try:
            transcript = registry.get(spliced_ref)
        except KeyError:
            return self._missing_input(task, spliced_ref)
        if transcript.molecule_type is not MoleculeType.SPLICED_TRANSCRIPT:
            return task.with_terminal(TaskState.FAILED, reason=f"{spliced_ref} is not a spliced transcript")

        protein_ref = f"protein.{self._suffix(spliced_ref)}"
        duplicate = self._add_structure(
            registry,
            task,
            MolecularStructure(
                ref=protein_ref,
                molecule_type=MoleculeType.PROTEIN,
                content=f"artifact fragment: {transcript.content}",
                source_refs=(spliced_ref,),
                markers=tuple(dict.fromkeys((*transcript.markers, "artifact_fragment"))),
            )
        )
        if duplicate is not None:
            return duplicate
        return task.with_terminal(
            TaskState.COMPLETE,
            reason="spliced transcript translated",
            outputs=(protein_ref,),
        )

    def _suffix(self, ref: str) -> str:
        return ref.split(".", 1)[1] if "." in ref else ref

    def _missing_input(self, task: MicroTask, ref: str) -> MicroTask:
        return task.with_terminal(
            TaskState.BLOCKED,
            reason=f"missing molecular input: {ref}",
        )

    def _add_structure(
        self,
        registry: MoleculeRegistry,
        task: MicroTask,
        structure: MolecularStructure,
    ) -> MicroTask | None:
        try:
            registry.add(structure)
        except ValueError as exc:
            if "duplicate molecular structure ref" not in str(exc):
                raise
            return task.with_terminal(
                TaskState.FAILED,
                reason=f"duplicate molecular output: {structure.ref}",
            )
        return None
