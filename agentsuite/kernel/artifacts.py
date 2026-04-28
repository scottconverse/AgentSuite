"""Artifact writer for AgentSuite runs."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from agentsuite.kernel.schema import ArtifactKind, ArtifactRef, Stage


class ArtifactWriter:
    """Persist run artifacts to disk with content-addressed SHA tracking."""

    def __init__(self, output_root: Path, run_id: str) -> None:
        """Initialize the writer with an output root and run ID.

        Args:
            output_root: Root directory where run subdirectories are created.
            run_id: Unique identifier for this run (used to create run_dir).
        """
        self.output_root = Path(output_root)
        self.run_id = run_id
        self.run_dir = self.output_root / "runs" / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._refs: list[ArtifactRef] = []

    def _resolve_safe(self, relative_path: str) -> Path:
        """Resolve relative_path to an absolute path within run_dir.

        Raises ValueError if the resolved path escapes run_dir (path traversal guard).
        """
        full = self.run_dir / relative_path
        full_resolved = full.resolve()
        run_dir_resolved = self.run_dir.resolve()
        if not full_resolved.is_relative_to(run_dir_resolved):
            raise ValueError(f"Artifact path escapes run_dir: {relative_path!r}")
        return full_resolved

    def write(
        self,
        relative_path: str,
        content: str,
        *,
        kind: ArtifactKind,
        stage: Stage,
    ) -> ArtifactRef:
        """Write text content to ``run_dir/relative_path`` and return an ArtifactRef.

        Idempotent: a second write to the same relative_path overwrites the file
        and replaces the in-memory ref with the new content hash.

        Args:
            relative_path: Path relative to run_dir (may include subdirectories).
            content: Text content to write.
            kind: Artifact classification (spec, brief, prompt, qa_report, template, data).
            stage: Pipeline stage (intake, extract, spec, execute, qa, approval, done).

        Returns:
            ArtifactRef with path, kind, stage, and SHA-256 hash of content.
        """
        full = self._resolve_safe(relative_path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        ref = ArtifactRef(path=full, kind=kind, stage=stage, sha256=sha)  # full is already resolved
        self._register(ref)
        return ref

    def write_json(
        self,
        relative_path: str,
        data: Any,
        *,
        kind: ArtifactKind,
        stage: Stage,
    ) -> ArtifactRef:
        """Serialize ``data`` as indented JSON and write via :meth:`write`.

        Args:
            relative_path: Path relative to run_dir.
            data: Python object to serialize (dict, list, etc).
            kind: Artifact classification.
            stage: Pipeline stage.

        Returns:
            ArtifactRef from the underlying write() call.
        """
        text = json.dumps(data, indent=2, default=str)
        return self.write(relative_path, text, kind=kind, stage=stage)

    def refs(self) -> list[ArtifactRef]:
        """Return a snapshot of all artifact refs registered for this run."""
        return list(self._refs)

    def _register(self, ref: ArtifactRef) -> None:
        """Register or update a ref in the internal list.

        If a ref for the same path exists, it is replaced (idempotency).
        """
        self._refs = [r for r in self._refs if r.path != ref.path]
        self._refs.append(ref)

    def promote(self, project_slug: str) -> list[Path]:
        """Copy run artifacts into ``_kernel/<project_slug>/`` for downstream agents.

        Skips files starting with underscore (``_state.json``, ``_meta.json``)
        since those are run-internal bookkeeping, not consumable artifacts.

        Args:
            project_slug: Project identifier (e.g. "patentforgelocal").

        Returns:
            List of promoted artifact paths in the _kernel directory.
        """
        target = self.output_root / "_kernel" / project_slug
        target.mkdir(parents=True, exist_ok=True)
        promoted: list[Path] = []
        for entry in self.run_dir.iterdir():
            if entry.name.startswith("_"):
                continue  # skip _state.json, _meta.json, etc.
            dest = target / entry.name
            if entry.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(entry, dest)
            else:
                shutil.copy2(entry, dest)
            promoted.append(dest)
        return promoted
