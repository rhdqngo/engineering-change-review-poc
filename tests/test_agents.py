from ecr_poc.adk_agent.agent import (
    engineering_review_agent,
    evidence_verifier_agent,
    root_agent,
)


def test_exactly_two_declared_roles_and_no_coordinator() -> None:
    roles = [
        engineering_review_agent,
        evidence_verifier_agent,
    ]
    assert [agent.name for agent in roles] == [
        "engineering_review",
        "evidence_verifier",
    ]
    assert all(agent.mode == "chat" for agent in roles)
    assert root_agent is engineering_review_agent
