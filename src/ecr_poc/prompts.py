from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .data import repository_root


class PromptBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    change_analyst: str
    engineering_review: str
    evidence_verifier: str


@lru_cache(maxsize=4)
def load_prompt_bundle(root: Path | None = None) -> PromptBundle:
    root = root or repository_root()
    path = root / "data" / "prompts" / "ecr-poc-v2.json"
    return PromptBundle.model_validate_json(path.read_text(encoding="utf-8"))
