from ecr_poc.adk_agent.agent import (
    change_analyst_agent,
    engineering_review_agent,
    evidence_verifier_agent,
    root_agent,
)


def test_exactly_three_declared_roles_and_no_coordinator() -> None:
    roles = [
        change_analyst_agent,
        engineering_review_agent,
        evidence_verifier_agent,
    ]
    assert [agent.name for agent in roles] == [
        "change_analyst",
        "engineering_review",
        "evidence_verifier",
    ]
    assert all(agent.mode == "chat" for agent in roles)
    assert root_agent is change_analyst_agent
