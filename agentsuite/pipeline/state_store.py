"""Persistence for pipeline state."""
from __future__ import annotations

from pathlib import Path

from agentsuite.pipeline.schema import PipelineState


class PipelineNotFound(KeyError):
    """Raised when a pipeline_id is not found on disk."""


class PipelineStateStore:
    def __init__(self, pipelines_root: Path, pipeline_id: str) -> None:
        self.pipeline_dir = pipelines_root / pipeline_id
        self.path = self.pipeline_dir / "_pipeline.json"

    def save(self, state: PipelineState) -> None:
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> PipelineState:
        if not self.path.exists():
            raise PipelineNotFound(self.pipeline_dir.name)
        return PipelineState.model_validate_json(self.path.read_text(encoding="utf-8"))
