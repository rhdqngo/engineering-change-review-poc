from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.genai import types

from ecr_poc.models import CandidateDecisionBatch, ClaimVerificationBatch
from ecr_poc.prompts import PromptBundle, load_prompt_bundle

MODEL = os.environ.get("ECR_LLM_MODEL", "gemini-3.5-flash")
GENERATION = types.GenerateContentConfig(temperature=0, max_output_tokens=65_536)


def make_engineering_reviewer(prompts: PromptBundle | None = None) -> LlmAgent:
    prompts = prompts or load_prompt_bundle()
    return LlmAgent(
        name="engineering_review",
        model=MODEL,
        description="Produces atomic impact claims within an immutable Final Top-10 docket.",
        instruction=prompts.engineering_review,
        output_schema=CandidateDecisionBatch,
        include_contents="none",
        mode="chat",
        generate_content_config=GENERATION,
    )


def make_evidence_verifier(prompts: PromptBundle | None = None) -> LlmAgent:
    prompts = prompts or load_prompt_bundle()
    return LlmAgent(
        name="evidence_verifier",
        model=MODEL,
        description="Independently verifies exact evidence support for atomic impact claims.",
        instruction=prompts.evidence_verifier,
        output_schema=ClaimVerificationBatch,
        include_contents="none",
        mode="chat",
        generate_content_config=GENERATION,
    )


engineering_review_agent = make_engineering_reviewer()
evidence_verifier_agent = make_evidence_verifier()

# ADK discovery requires one root. It is the Engineering Reviewer, not a coordinator.
root_agent = engineering_review_agent
