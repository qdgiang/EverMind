"""Owner: A. GET /decisions (DSH-4 filters + show_inactive)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.api.deps import get_session
from evermind.contracts.enums import DecisionStatus
from evermind.decisions.models import Decision
from evermind.org.models import User

router = APIRouter(tags=["decisions"])


@router.get("/decisions")
def list_decisions(
    session: Session = Depends(get_session),
    scope: str | None = None,
    q: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    user: str | None = None,
    show_inactive: bool = False,
):
    """Decision log with the documented read filters.

    The wire shape deliberately uses an actor handle rather than exposing the
    dashboard's internal numeric persona convention.
    """
    stmt = select(Decision, User.handle).join(User, User.id == Decision.decided_by_user_id)
    if not show_inactive:
        stmt = stmt.where(Decision.status.in_((DecisionStatus.PROPOSED, DecisionStatus.EFFECTIVE)))
    if scope is not None:
        stmt = stmt.where(Decision.scope == scope)
    if q is not None:
        stmt = stmt.where(Decision.description.ilike(f"%{q}%"))
    if user is not None:
        stmt = stmt.where(User.handle == user)
    if from_ is not None:
        stmt = stmt.where(Decision.ts >= _parse_timestamp(from_, "from"))
    if to is not None:
        stmt = stmt.where(Decision.ts <= _parse_timestamp(to, "to"))

    rows = session.execute(stmt.order_by(Decision.ts.desc(), Decision.id.desc())).all()
    return [
        {
            "id": decision.id,
            "description": decision.description,
            "status": decision.status.value,
            "decided_by": handle,
            "ts": decision.ts,
            "superseded_by_decision_id": decision.superseded_by_decision_id,
        }
        for decision, handle in rows
    ]


def _parse_timestamp(value: str, parameter: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{parameter} must be an ISO-8601 timestamp",
        ) from exc
