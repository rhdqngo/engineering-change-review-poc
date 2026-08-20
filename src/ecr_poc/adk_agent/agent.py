from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.genai import types

from ecr_poc.models import ReviewBatch, StructuredChange, VerificationBatch
from ecr_poc.prompts import PromptBundle, load_prompt_bundle

MODEL = os.environ.get("ECR_LLM_MODEL", "gemini-3.5-flash")
GENERATION = types.GenerateContentConfig(temperature=0, max_output_tokens=8192)


def make_change_analyst(prompts: PromptBundle | None = None) -> LlmAgent:
    prompts = prompts or load_prompt_bundle()
    return LlmAgent(
        name="change_analyst",
        model=MODEL,
        description="Normalizes one engineering change without selecting review artifacts.",
        instruction=prompts.change_analyst,
        output_schema=StructuredChange,
        include_contents="none",
        mode="chat",
        generate_content_config=GENERATION,
    )


def make_engineering_reviewer(prompts: PromptBundle | None = None) -> LlmAgent:
    prompts = prompts or load_prompt_bundle()
    return LlmAgent(
        name="engineering_review",
        model=MODEL,
        description="Selects actual review needs within a fixed candidate set.",
        instruction=prompts.engineering_review,
        output_schema=ReviewBatch,
        include_contents="none",
        mode="chat",
        generate_content_config=GENERATION,
    )


def make_evidence_verifier(prompts: PromptBundle | None = None) -> LlmAgent:
    prompts = prompts or load_prompt_bundle()
    return LlmAgent(
        name="evidence_verifier",
        model=MODEL,
        description="Independently checks whether exact evidence supports each review reason.",
        instruction=prompts.evidence_verifier,
        output_schema=VerificationBatch,
        include_contents="none",
        mode="chat",
        generate_content_config=GENERATION,
    )


change_analyst_agent = make_change_analyst()
engineering_review_agent = make_engineering_reviewer()
evidence_verifier_agent = make_evidence_verifier()

# ADK requires one exported root for discovery. It is one of the three declared
# roles, not a fourth coordinator. The evaluation runner invokes the three role
# instances explicitly around the sealed retrieval result.
root_agent = change_analyst_agent
