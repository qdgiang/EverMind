"""L1 — write plumbing ([EVM-021], [EVM-002] gateway side) + TSK-2 update-lane
routing at the gateway (interface #9) + domain-event append (D3)."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from evermind.contracts.commands import RecordSignal, RecordTaskUpdate
from evermind.contracts.enums import CreatedFrom, TaskStatus
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, ProcessedCommand


def test_command_idempotency_same_id_one_event(service, task_port, org_ids, mk,
                                               db_session):
    """[EVM-021]: the same client_command_id twice ⇒ ONE decision, one event
    set; the retry returns the recorded outcome."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    command = mk.propose(linh, [mk.op_set("task:1", "attr:venue", "school")])

    first = service.handle(command)
    second = service.handle(command)
    assert first["status"] == "effective"
    assert second["decision_id"] == first["decision_id"]
    assert second["duplicate"] is True
    assert db_session.query(Decision).count() == 1
    effective_events = db_session.query(DomainEvent).filter(
        DomainEvent.kind == "decision_effective").count()
    assert effective_events == 1


def test_expected_version_mismatch_conflicts(service, task_port, org_ids, mk, db_session):
    """[EVM-021]: a stale dashboard form (wrong expected_version) gets the
    409-shaped diff card — never a silent overwrite. Nothing is written."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    standing = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:venue", "school")]))

    stale = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")],
        created_from=CreatedFrom.DASHBOARD,
        expected_version="999"))  # the form was rendered against a ghost
    assert stale["status"] == "version_conflict"
    assert stale["diff"][0]["current_decision_id"] == standing["decision_id"]
    assert db_session.query(Decision).count() == 1  # no write happened

    fresh = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")],
        created_from=CreatedFrom.DASHBOARD,
        expected_version=str(standing["decision_id"])))
    assert fresh["status"] == "effective"


def test_expected_vacant(service, task_port, org_ids, mk):
    """[EVM-021]: `vacant` asserts no standing decision; occupied ⇒ conflict."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    ok = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "school")],
        created_from=CreatedFrom.DASHBOARD, expected_version="vacant"))
    assert ok["status"] == "effective"

    conflict = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")],
        created_from=CreatedFrom.DASHBOARD, expected_version="vacant"))
    assert conflict["status"] == "version_conflict"


def test_outcome_recorded_for_replay(service, task_port, org_ids, mk, db_session):
    """[EVM-021]: processed_commands stores the outcome — the retry's source."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    command = mk.propose(linh, [mk.op_set("task:1", "attr:venue", "school")])
    outcome = service.handle(command)
    row = db_session.get(ProcessedCommand, str(command.client_command_id))
    assert row is not None
    assert row.outcome["decision_id"] == outcome["decision_id"]


def test_domain_events_appended_same_transaction(service, task_port, org_ids, mk,
                                                 db_session):
    """D3: every state change appends domain_events — the ONLY projection input."""
    duc = org_ids["users"]["duc"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    pending = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:x", 1)], created_from=CreatedFrom.LLM,
        confidence=0.9))
    kinds = [e.kind for e in db_session.scalars(select(DomainEvent))]
    assert "decision_proposed" in kinds
    events = list(db_session.scalars(select(DomainEvent).where(
        DomainEvent.kind == "decision_proposed")))
    assert events[0].payload["decision_id"] == pending["decision_id"]
    assert events[0].caused_by_command is not None


# ── TSK-2 update-lane routing (the gateway half; B's fold consumes) ─────────


def _update(actor: int, task_id: int, kind: str = "status",
            payload: dict | None = None) -> RecordTaskUpdate:
    return RecordTaskUpdate(
        client_command_id=uuid.uuid4(), persona=f"user-{actor}",
        created_from=CreatedFrom.LLM, confidence=0.9, task_id=task_id,
        actor_user_id=actor, update_kind=kind,
        payload=payload or {"status": "doing"})


def test_pic_update_auto_applies(service, task_port, org_ids):
    """G7: the cited author is a PIC ⇒ auto-apply lane."""
    duc = org_ids["users"]["duc"]
    task_port.add(1, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"]], pics=[duc])
    outcome = service.handle(_update(duc, 1))
    assert outcome == {"status": "applied", "task_id": 1, "lane": "pic_auto"}


def test_authority_update_decision_grade(service, task_port, org_ids):
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"]], pics=[])
    outcome = service.handle(_update(linh, 1))
    assert outcome["lane"] == "authority"


def test_third_party_update_needs_pic_confirm(service, task_port, org_ids, db_session):
    """G9: anyone else ⇒ a PIC confirm card, nothing applied."""
    tuan, duc = org_ids["users"]["tuan"], org_ids["users"]["duc"]
    task_port.add(1, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"]], pics=[duc])
    outcome = service.handle(_update(tuan, 1))
    assert outcome["status"] == "pending_confirm"
    assert outcome["confirmers"] == [duc]
    kinds = [e.kind for e in db_session.scalars(select(DomainEvent))]
    assert "task_update_pending_confirm" in kinds
    assert "task_update_recorded" not in kinds


def test_terminal_lock_names_canceling_decision(service, task_port, org_ids, mk):
    """TSK-6/G52: a status update on a canceled task is locked, and the lock
    names the canceling decision."""
    linh, duc = org_ids["users"]["linh"], org_ids["users"]["duc"]
    task_port.add(1, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"]], pics=[duc])
    cancel = service.handle(mk.propose(linh, [mk.op_set("task:1", "status", "canceled")]))
    task_port.tasks[1].status = TaskStatus.CANCELED

    outcome = service.handle(_update(duc, 1, kind="status", payload={"status": "done"}))
    assert outcome["status"] == "terminal_locked"
    assert outcome["canceling_decision_id"] == cancel["decision_id"]


def test_merged_husk_redirects_to_survivor(service, task_port, org_ids):
    """G52: ops aimed at a merged husk auto-redirect to the survivor."""
    duc = org_ids["users"]["duc"]
    task_port.add(3, org_ids["projects"]["P-TT"], status="merged", merged_into=4)
    task_port.add(4, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"]], pics=[duc])
    outcome = service.handle(_update(duc, 3, kind="note", payload={"note": "hi"}))
    assert outcome["status"] == "applied"
    assert outcome["task_id"] == 4


def test_record_signal_appends_event_only(service, org_ids, db_session):
    """SIG-1 gateway half: signals enter as events with the [EVM-013] identity
    key in the payload; B's ledger folds them."""
    outcome = service.handle(RecordSignal(
        client_command_id=uuid.uuid4(), persona="user-duc",
        created_from=CreatedFrom.LLM, confidence=0.7,
        source_message_id=77, window_id=2,
        signal_kind="blocker", project_id=org_ids["projects"]["P-TT"],
        task_id=None, party_id=None,
        normalized_topic="giấy phép phường", excerpt="vẫn chưa có giấy phép..."))
    assert outcome["status"] == "signal_recorded"
    event = db_session.scalar(select(DomainEvent).where(
        DomainEvent.kind == "signal_recorded"))
    assert event.payload["normalized_topic"] == "giấy phép phường"
    assert event.payload["message_id"] == 77
