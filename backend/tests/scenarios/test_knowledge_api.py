"""KNW-1/2 — structured, cited answer over effective decisions."""
from __future__ import annotations

from evermind.knowledge.service import KnowledgeService


def test_keyword_answer_returns_effective_decision_with_receipt(service, task_port, org_ids, mk, db_session):
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    outcome = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "Nguyen Du")],
        description="Hold the fair at Nguyen Du",
    ))

    answer = KnowledgeService(db_session).answer("Where is the fair? Nguyen Du", "linh")

    assert "Hold the fair at Nguyen Du" in answer["answer"]
    assert answer["citations"] == [{"decision_id": outcome["decision_id"], "message_ids": [1]}]
