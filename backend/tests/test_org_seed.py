"""P0 — OPS-1 org seed loader + org service v0 (data-v2/org.json, [D5], G44)."""
from __future__ import annotations

from evermind.org.service import OrgService


def test_seed_loads_and_maps(org_ids, org: OrgService):
    assert set(org_ids["projects"]) == {"P-TT", "P-CL", "P-LIVE"}
    assert set(org_ids["teams"]) == {"TEAM-EV", "TEAM-ED", "TEAM-LIVE"}
    assert len(org_ids["users"]) == 9
    assert "trang" not in org_ids["users"]  # she must arrive provisionally (G44)
    # the live telegram group stays a FILL_ME placeholder until its real chat id
    # is pasted in (runbook §Telegram) — the seed must skip it, not create it
    assert "G-LIVE" not in org_ids["groups"]

    linh = org.get_user_by_handle("linh")
    assert linh.role_rank == 3  # linh is coordinator
    assert org.coordinator().id == linh.id

    mai = org.get_user_by_handle("mai")
    assert org.manager_chain(mai.id) == [linh.id]
    assert org.lead_of_team(org_ids["teams"]["TEAM-ED"]) == mai.id

    # matrix members (khoa, thao) hold multiple user_teams rows (G36)
    khoa = org.get_user_by_handle("khoa")
    thao = org.get_user_by_handle("thao")
    assert len(org.teams_of_user(khoa.id)) == 2
    assert len(org.teams_of_user(thao.id)) == 2


def test_seed_is_idempotent(db_session, org_ids):
    """Running the seed twice never duplicates (natural-key upsert)."""
    from tests.conftest import ORG_SEED_PATH
    from evermind.org.seed import load_org_seed

    again = load_org_seed(db_session, ORG_SEED_PATH)
    assert again["users"] == org_ids["users"]
    assert again["projects"] == org_ids["projects"]


def test_party_alias_match(org_ids, org: OrgService):
    party = org.match_party_alias("đang chờ chị Yến trả lời")
    assert party is not None and party.name == "chị Yến"
    assert org.match_party_alias("hỏi bên Kim Long chưa?").name == "Xưởng Kim Long"
    assert org.match_party_alias("something unrelated entirely-xyz") is None


def test_provisional_arrival_and_rejoin(org_ids, org: OrgService):
    """G44/G69: first unknown platform id ⇒ provisional user; rejoin reuses the
    known id — never a duplicate."""
    trang = org.create_provisional_user(
        name="Trang", platform="generic-chat", connector_scope="default",
        platform_user_id="u2001", team_id=org_ids["teams"]["TEAM-EV"])
    assert trang.status.value == "provisional"
    assert trang.role_rank == 1

    again = org.create_provisional_user(
        name="Trang Nguyen", platform="generic-chat", connector_scope="default",
        platform_user_id="u2001")
    assert again.id == trang.id  # rejoin reuses the identity

    confirmed = org.confirm_membership(trang.id, actor="mai")
    assert confirmed.status.value == "active"


def test_personas_hide_departed(org_ids, org: OrgService, db_session):
    from evermind.contracts.enums import UserStatus

    tuan = org.get_user_by_handle("tuan")
    tuan.status = UserStatus.DEPARTED
    db_session.flush()
    handles = {u.handle for u in org.list_personas()}
    assert "tuan" not in handles
    assert "linh" in handles
