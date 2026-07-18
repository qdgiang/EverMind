"""L3 — API contract regressions for the dashboard's persona/read surface."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from evermind.api.deps import persona, persona_user_id
from evermind.api.routers.decisions_router import list_decisions


def test_persona_wire_value_is_a_handle_not_numeric_id(db_session, org_ids):
    assert persona("linh", db_session) == "linh"
    assert persona_user_id("linh", db_session) == org_ids["users"]["linh"]

    with pytest.raises(HTTPException, match="unknown persona '1'"):
        persona("1", db_session)


def test_decisions_router_lists_effective_decisions_and_hides_inactive_by_default(
    db_session, service, task_port, org_ids, mk,
):
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])

    first = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "Nguyen Du")],
        description="Use Nguyen Du venue",
    ))
    second = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "Kim Lien")],
        description="Move venue to Kim Lien",
    ))

    visible = list_decisions(session=db_session, q="Kim Lien")
    assert [row["id"] for row in visible] == [second["decision_id"]]
    assert visible[0]["status"] == "effective"
    assert visible[0]["decided_by"] == "linh"

    all_rows = list_decisions(session=db_session, show_inactive=True)
    statuses = {row["id"]: row["status"] for row in all_rows}
    assert statuses[first["decision_id"]] == "superseded"
    assert statuses[second["decision_id"]] == "effective"
