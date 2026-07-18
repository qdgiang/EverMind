"""Owner: A. App assembly — architecture.md §API surface. Module routers stay
with their owning module; this file only mounts them + the `POST /commands`
front door (kept literal on purpose: no business logic may grow here).
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from evermind.api.deps import decisions_service, persona
from evermind.api.routers import (
    connectors_router,
    decisions_router,
    knowledge_router,
    org_router,
    signals_router,
    surfacing_router,
    tasks_router,
)
from evermind.contracts.commands import Command
from evermind.decisions.service import DecisionsService

app = FastAPI(title="EverMind API")

app.include_router(org_router.router)
app.include_router(decisions_router.router)
app.include_router(tasks_router.router)
app.include_router(signals_router.router)
app.include_router(surfacing_router.router)
app.include_router(connectors_router.router)
app.include_router(knowledge_router.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/commands")
def post_command(
    command: Command,
    service: DecisionsService = Depends(decisions_service),
    who: str = Depends(persona),
):
    """The single write path for every surface (D3). Validates + persona-stamps,
    hands straight to the domain — see architecture.md §The write pipeline.
    [EVM-021]: a `version_conflict` outcome renders as HTTP 409 + diff card.
    """
    if command.persona != who:
        command = command.model_copy(update={"persona": who})  # persona-stamp
    outcome = service.handle(command)
    if outcome.get("status") == "version_conflict":
        raise HTTPException(status_code=409, detail=outcome)
    return outcome
