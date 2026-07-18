"""Owner: A. GET /personas — seeded users for the FE switcher (DSH-1)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from evermind.api.deps import get_session
from evermind.org.service import OrgService

router = APIRouter(tags=["org"])


@router.get("/personas")
def list_personas(session: Session = Depends(get_session)):
    """Every seeded user except `departed` (design-v2 §Users lifecycle).
    Settled #3: the switcher is honest about being unauthenticated."""
    users = OrgService(session).list_personas()
    return [
        {
            "id": user.id,
            "handle": user.handle,
            "name": user.name,
            "role_rank": user.role_rank,
            "status": user.status.value,
        }
        for user in users
    ]
