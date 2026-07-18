from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from evermind.contracts.commands import (
    AppendCorroboration,
    CitationSpec,
    OpSpec,
    ProposeDecision,
    RecordSignal,
    RegisterReactionAct,
)
from evermind.contracts.enums import CitationKind, CreatedFrom, DecisionScope
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, DecisionCitation, ProcessedCommand
from evermind.decisions.service import DecisionsService
from tests.scenarios.test_lifecycle_basics import (
    FakeTaskStatePort,
    _context,
    _propose,
    _seed_org,
)


def test_command_idempotency_is_persona_safe_and_never_replays_an_outcome_to_an_impostor(
    db_session: Session,
) -> None:
    """EVM-021: one command id means one event, but its receipt is persona-bound."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    command = _propose(
        command_id="00000000-0000-0000-0000-000000000101",
        persona="joe",
        actor=302,
        value="apples",
    )
    first = service.handle(command, context=_context(event_id="evt-idempotent", hour=9))
    retried = service.handle(command, context=_context(event_id="evt-retry", hour=10))
    impostor = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000101",
            persona="jack",
            actor=304,
            value="peaches",
        ),
        context=_context(event_id="evt-impostor", hour=11),
    )

    assert retried == first
    assert impostor == {
        "ok": False,
        "status": "forbidden",
        "http_status": 403,
        "error": "client_command_id belongs to another persona",
    }
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 1
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 1


def test_expected_version_conflict_is_deterministic_and_has_no_domain_side_effect(
    db_session: Session,
) -> None:
    """EVM-021: stale writes return 409+diff and are idempotently receipted."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    standing = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000102",
            persona="joe",
            actor=302,
            value="apples",
        ),
        context=_context(event_id="evt-version-standing", hour=9),
    )
    stale = _propose(
        command_id="00000000-0000-0000-0000-000000000103",
        persona="joe",
        actor=302,
        value="peaches",
    ).model_copy(update={"expected_version": "v1:stale"})
    conflict = service.handle(stale, context=_context(event_id="evt-version-stale", hour=10))
    retried = service.handle(stale, context=_context(event_id="evt-version-retry", hour=11))

    assert conflict == {
        "ok": False,
        "status": "version_conflict",
        "http_status": 409,
        "expected_version": "v1:stale",
        "current_version": standing["version"],
        "diff": {"v1|task:501|attr:fruit": standing["decision_id"]},
    }
    assert retried == conflict
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 1
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 2


def test_signal_corroboration_and_tracked_reaction_commands_all_route_to_events(
    db_session: Session,
) -> None:
    """P1 gateway: frozen signal/corroboration/reaction commands each append one event."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    standing = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000104",
            persona="joe",
            actor=302,
            value="apples",
        ),
        context=_context(event_id="evt-route-standing", hour=9),
    )
    corroborated = service.handle(
        AppendCorroboration(
            client_command_id=UUID("00000000-0000-0000-0000-000000000105"),
            persona="jack",
            created_from=CreatedFrom.MARKER,
            source_message_id=8401,
            decision_id=standing["decision_id"],
            citation=CitationSpec(
                message_id=8401,
                kind=CitationKind.CORROBORATION,
                rev_at_capture=1,
            ),
        ),
        context=_context(event_id="evt-route-corroboration", hour=10),
    )
    pending = service.handle(
        ProposeDecision(
            client_command_id=UUID("00000000-0000-0000-0000-000000000106"),
            persona="jack",
            created_from=CreatedFrom.MARKER,
            source_message_id=8402,
            decided_by_user_id=304,
            scope=DecisionScope.TASK,
            scope_target="task:501",
            description="Change quantity",
            ops=[OpSpec(target="task:501", facet="attr:quantity", op="set", value=50)],
            citations=[
                CitationSpec(
                    message_id=8402,
                    kind=CitationKind.EVIDENCE,
                    rev_at_capture=1,
                )
            ],
        ),
        context=_context(
            event_id="evt-route-pending",
            hour=11,
            citation_authors={8402: 304},
        ),
    )
    reaction = service.handle(
        RegisterReactionAct(
            client_command_id=UUID("00000000-0000-0000-0000-000000000107"),
            persona="joe",
            created_from=CreatedFrom.MARKER,
            message_id=8402,
            user_id=302,
            emoji="👍",
        ),
        context=_context(event_id="evt-route-reaction", hour=12),
    )
    signal = service.handle(
        RecordSignal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000108"),
            persona="joe",
            created_from=CreatedFrom.MARKER,
            source_message_id=8403,
            signal_kind="blocker",
            project_id=101,
            task_id=501,
            normalized_topic="venue permit",
            excerpt="Permit is late",
        ),
        context=_context(event_id="evt-route-signal", hour=13),
    )
    untracked = service.handle(
        RegisterReactionAct(
            client_command_id=UUID("00000000-0000-0000-0000-000000000109"),
            persona="joe",
            created_from=CreatedFrom.MARKER,
            message_id=9999,
            user_id=302,
            emoji="👍",
        ),
        context=_context(event_id="evt-untracked-reaction", hour=14),
    )

    assert corroborated["status"] == "corroborated"
    assert pending["status"] == "proposed"
    assert reaction["status"] == "recorded"
    assert signal["status"] == "recorded"
    assert untracked == {
        "ok": False,
        "status": "invalid",
        "http_status": 422,
        "error": "reaction message is not tracked",
    }
    citation = db_session.scalar(
        select(DecisionCitation).where(DecisionCitation.message_id == 8401)
    )
    assert citation.kind is CitationKind.CORROBORATION
    assert list(db_session.scalars(select(DomainEvent.kind).order_by(DomainEvent.seq))) == [
        "decision_effective",
        "corroboration_appended",
        "decision_proposed",
        "reaction_act_registered",
        "signal_recorded",
    ]
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 5
