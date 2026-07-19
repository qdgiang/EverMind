"""Project-scoped, authorized blocker board."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from evermind.api.deps import get_session, persona_user_id
from evermind.org.service import OrgService
from evermind.tasks.service import TasksService

router = APIRouter(tags=["signals"])


@router.get("/blockers")
def list_blockers(project_id: int, session: Session = Depends(get_session),
                  viewer_id: int = Depends(persona_user_id)):
    org = OrgService(session)
    if org.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="unknown project")
    if not org.can_view_project(viewer_id, project_id):
        raise HTTPException(status_code=403, detail="persona is not a member of this project")
    groups: dict[tuple[int | None, str | None], list[dict]] = {}
    for task in TasksService(session).list_tasks(project_id=project_id, statuses=("blocked",)):
        groups.setdefault((task.blocked_waiting_on_party_id, task.blocked_waiting_on_text), []).append({
            "task_id": task.id, "description": task.description, "since": task.blocked_since,
        })
    output = []
    for (party_id, text), tasks in groups.items():
        party = org.get_party(party_id) if party_id is not None else None
        output.append({"waiting_on": {"party_id": party_id, "name": party.name if party else None, "text": text},
                       "tasks": sorted(tasks, key=lambda t: (t["since"] or "", t["task_id"]))})
    return {"groups": sorted(output, key=lambda g: (g["waiting_on"]["name"] or g["waiting_on"]["text"] or "", g["waiting_on"]["party_id"] or 0))}
