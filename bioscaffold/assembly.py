from __future__ import annotations

from dataclasses import dataclass

from bioscaffold.microtasks import AgentHat, BioScale, MicroOperation, MicroTask, TaskState
from bioscaffold.molecules import MolecularStructure, MoleculeRegistry, MoleculeType


@dataclass(frozen=True)
class ProductAssemblyResult:
    tasks: tuple[MicroTask, ...]
    module_ref: str
    subsystem_ref: str
    capability_ref: str
    assembly_refs: tuple[str, ...]


class ProductAssemblyEngine:
    def assemble(
        self,
        registry: MoleculeRegistry,
        *,
        organism_id: str,
        artifact_refs: tuple[str, ...],
    ) -> ProductAssemblyResult:
        if not artifact_refs:
            return ProductAssemblyResult(
                tasks=(),
                module_ref="",
                subsystem_ref="",
                capability_ref="",
                assembly_refs=(),
            )

        module_ref = f"module.{organism_id}.v1"
        subsystem_ref = f"subsystem.{organism_id}.v1"
        capability_ref = f"capability.{organism_id}.v1"
        module = self._add_structure(
            registry,
            MolecularStructure(
                ref=module_ref,
                molecule_type=MoleculeType.MODULE,
                content="module assembled from validated artifact fragments",
                source_refs=artifact_refs,
                markers=("assembled_module",),
            ),
        )
        subsystem = self._add_structure(
            registry,
            MolecularStructure(
                ref=subsystem_ref,
                molecule_type=MoleculeType.SUBSYSTEM,
                content="subsystem assembled from product module",
                source_refs=(module_ref,),
                markers=("assembled_subsystem",),
            ),
        )
        capability = self._add_structure(
            registry,
            MolecularStructure(
                ref=capability_ref,
                molecule_type=MoleculeType.CAPABILITY,
                content="capability assembled from product subsystem",
                source_refs=(subsystem_ref,),
                markers=("product_capability",),
            ),
        )
        tasks = (
            self._promotion_task(
                task_id=f"task.assemble.{module_ref}",
                organism_id=organism_id,
                scale=BioScale.CELL,
                target_ref=",".join(artifact_refs),
                output_ref=module.ref,
                expected_output="module",
                reason="validated artifacts promoted to module",
            ),
            self._promotion_task(
                task_id=f"task.assemble.{subsystem_ref}",
                organism_id=organism_id,
                scale=BioScale.TISSUE,
                target_ref=module_ref,
                output_ref=subsystem.ref,
                expected_output="subsystem",
                reason="module promoted to subsystem",
            ),
            self._promotion_task(
                task_id=f"task.assemble.{capability_ref}",
                organism_id=organism_id,
                scale=BioScale.ORGAN,
                target_ref=subsystem_ref,
                output_ref=capability.ref,
                expected_output="capability",
                reason="subsystem promoted to capability",
            ),
        )
        return ProductAssemblyResult(
            tasks=tasks,
            module_ref=module_ref,
            subsystem_ref=subsystem_ref,
            capability_ref=capability_ref,
            assembly_refs=(module_ref, subsystem_ref, capability_ref),
        )

    def _add_structure(
        self,
        registry: MoleculeRegistry,
        structure: MolecularStructure,
    ) -> MolecularStructure:
        try:
            return registry.add(structure)
        except ValueError as exc:
            if "duplicate molecular structure ref" not in str(exc):
                raise
            return registry.get(structure.ref)

    def _promotion_task(
        self,
        *,
        task_id: str,
        organism_id: str,
        scale: BioScale,
        target_ref: str,
        output_ref: str,
        expected_output: str,
        reason: str,
    ) -> MicroTask:
        return MicroTask(
            task_id=task_id,
            turn_id="assembly",
            generation_id="assembly",
            organism_id=organism_id,
            scale=scale,
            operation=MicroOperation.PROMOTE,
            target_ref=target_ref,
            agent_hat=AgentHat.GENERATION_REVIEWER,
            expected_output=expected_output,
            metadata={"project_workflow": True, "workflow_phase": "assembly"},
        ).with_terminal(
            TaskState.COMPLETE,
            reason=reason,
            outputs=(output_ref,),
        )
