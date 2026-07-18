"""Cross-module port *shapes* (typing only — no logic, no IO, no imports of modules).

Why here: `decisions` (A) may import only `contracts` + `org` (architecture.md
import rule), yet the gateway needs two reads of B's `tasks` projection
(work-split.md interface #9):
  1. update-lane routing — "is the cited author a PIC?" (TSK-2)
  2. approval-time revalidation — terminal state / merged survivor (G52)

So the *protocol* lives in contracts; B implements it on `tasks.service`; the
`api` layer (which may import both service ports) wires the implementation into
`DecisionsService`. Tests inject fakes.
"""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from evermind.contracts.enums import TaskStatus


class TaskView(BaseModel):
    """The slice of the tasks projection the decision gateway may read."""

    id: int
    project_id: int
    status: TaskStatus
    team_ids: list[int] = []
    pic_user_ids: list[int] = []
    merged_into: int | None = None


class TaskReadPort(Protocol):
    """Read-only. B's `tasks.service` provides this (interface #9)."""

    def get_task_view(self, task_id: int) -> TaskView | None: ...
