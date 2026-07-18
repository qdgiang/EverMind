"""Owner: B. Feed, inbox, digest, close-out, on/offboarding
(SRF-1..6, plan.md P4/P6).

SRF-1/2/3 (this phase) are built against what actually exists today: `tasks`
(real, P1) and `signals` (real, P2/P3). The decision-log/pending-proposal
sections that design-v2.md's digest also calls for need `decisions`
(DEC-1..9, Lane A, not built) — those sections are explicit TODOs below, not
guessed at.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.signals.service import SignalsService
from evermind.surfacing.models import FeedEntry, InboxItem
from evermind.tasks.models import Task, TaskTeam, TaskUpdate
from evermind.tasks.service import TasksService

FEED_BATCH_MINUTES = 30


class SurfacingService:
    def __init__(self, session: Session):
        self.session = session

    # -- SRF-1: feed -------------------------------------------------------

    def add_feed_entry(self, *, persona_user_id: int, kind: str, payload: dict,
                        batch_key: str, ts: datetime | None = None,
                        decision_id: int | None = None, task_id: int | None = None) -> int:
        """Batched (~30min) + deduped per (persona, batch_key): a second call
        inside the window returns the existing entry instead of duplicating
        (design-v2.md §Notifications). Retractions use `record_retraction`
        instead — they always append, never dedup.
        """
        ts = ts or datetime.now(timezone.utc)
        window_start = ts - timedelta(minutes=FEED_BATCH_MINUTES)
        existing = self.session.scalars(
            select(FeedEntry)
            .where(FeedEntry.persona_user_id == persona_user_id)
            .where(FeedEntry.batch_key == batch_key)
            .where(FeedEntry.ts >= window_start)
        ).first()
        if existing is not None:
            return existing.id

        entry = FeedEntry(
            persona_user_id=persona_user_id, ts=ts, kind=kind, decision_id=decision_id,
            task_id=task_id, payload=payload, batch_key=batch_key,
        )
        self.session.add(entry)
        self.session.flush()
        return entry.id

    def record_retraction(self, original_entry_id: int, *, payload: dict,
                           ts: datetime | None = None) -> int:
        """Symmetry rule (design-v2.md): anything asserted gets a matching
        withdrawal. Retractions APPEND a new entry and link back — the
        original never disappears or gets edited in place.
        """
        original = self.session.get(FeedEntry, original_entry_id)
        if original is None:
            raise LookupError(f"feed entry {original_entry_id} not found")
        retraction = FeedEntry(
            persona_user_id=original.persona_user_id, ts=ts or datetime.now(timezone.utc),
            kind="retraction", decision_id=original.decision_id, task_id=original.task_id,
            payload=payload, batch_key=f"retraction:{original_entry_id}",
        )
        self.session.add(retraction)
        self.session.flush()
        original.superseded_by_entry = retraction.id
        return retraction.id

    def feed_for(self, persona_user_id: int) -> list[FeedEntry]:
        return list(
            self.session.scalars(
                select(FeedEntry)
                .where(FeedEntry.persona_user_id == persona_user_id)
                .order_by(FeedEntry.ts.desc())
            )
        )

    def raise_radar_lamps_to_feed(self, *, project_id: int | None = None,
                                    now: datetime | None = None) -> int:
        """Wires SIG-3's output into the feed: one entry per (task, lamp, day),
        addressed to every current PIC. Team-lead/coordinator fallback for
        PIC-less tasks needs `org.service` (Lane A) — not wired yet (G56's
        "unowned work" case degrades to: no feed entry, task still shows in
        `radar_sweep()`'s raw output for anyone polling it directly).
        """
        now = now or datetime.now(timezone.utc)
        tasks_service = TasksService(self.session)
        entries = SignalsService(self.session).radar_sweep(project_id=project_id, now=now)
        count = 0
        for entry in entries:
            task_id, lamp = entry["task_id"], entry["lamp"]
            for pic_user_id in tasks_service.pics_of(task_id):
                self.add_feed_entry(
                    persona_user_id=pic_user_id, kind=f"lamp:{lamp}",
                    payload={"task_id": task_id, "lamp": lamp}, task_id=task_id, ts=now,
                    batch_key=f"radar:{task_id}:{lamp}:{now.date().isoformat()}",
                )
                count += 1
        return count

    # -- SRF-2: inbox --------------------------------------------------

    def add_inbox_item(self, *, persona_user_id: int, kind: str, ref_id: int,
                        created_at: datetime | None = None) -> int:
        """Generic writer — the actual triggers (proposal filed, G44 confirm
        card, challenge, diff, UNLINKED triage) are `decisions`/`ingestion`
        events (Lane A, not built); this is the landing spot for them.
        """
        item = InboxItem(
            persona_user_id=persona_user_id, kind=kind, ref_id=ref_id,
            created_at=created_at or datetime.now(timezone.utc),
        )
        self.session.add(item)
        self.session.flush()
        return item.id

    def resolve_inbox_item(self, item_id: int, *, resolution: str,
                            resolved_at: datetime | None = None) -> None:
        item = self.session.get(InboxItem, item_id)
        if item is None:
            raise LookupError(f"inbox item {item_id} not found")
        item.resolved_at = resolved_at or datetime.now(timezone.utc)
        item.resolution = resolution

    def inbox_for(self, persona_user_id: int, *, include_resolved: bool = False) -> list[InboxItem]:
        stmt = select(InboxItem).where(InboxItem.persona_user_id == persona_user_id)
        if not include_resolved:
            stmt = stmt.where(InboxItem.resolved_at.is_(None))
        return list(self.session.scalars(stmt.order_by(InboxItem.created_at.desc())))

    # -- SRF-3: digest ---------------------------------------------------

    def digest_for(self, team_id: int, *, now: datetime | None = None) -> dict:
        """Sections actually computable today: tasks (by status), open
        blockers, needs-attention (radar lamps), latest team-scoped wrap note
        (verbatim quote, G34). `decisions` (task+policy log, pending
        proposals) and `parked/asks aging` need `decisions`/`signals` P3-
        promoted state routed through Lane A — TODO once DEC-1..9 exists.
        """
        now = now or datetime.now(timezone.utc)
        task_ids = list(
            self.session.scalars(select(TaskTeam.task_id).where(TaskTeam.team_id == team_id))
        )
        tasks: list[Task] = []
        for tid in task_ids:
            task = self.session.get(Task, tid)
            if task is not None:
                tasks.append(task)

        by_status: dict[str, int] = {}
        for task in tasks:
            by_status[task.status] = by_status.get(task.status, 0) + 1

        blockers = [t for t in tasks if t.status == "blocked"]
        needs_attention = SignalsService(self.session).radar_sweep(now=now)
        needs_attention = [e for e in needs_attention if e["task_id"] in task_ids]

        wrap_note = self.session.scalars(
            select(TaskUpdate)
            .where(TaskUpdate.task_id.in_(task_ids))
            .where(TaskUpdate.kind == "note")
            .order_by(TaskUpdate.ts.desc())
        ).first()

        return {
            "team_id": team_id,
            "generated_at": now,
            "tasks_by_status": by_status,
            "blockers": [{"task_id": t.id, "description": t.description,
                          "waiting_on_text": t.blocked_waiting_on_text,
                          "waiting_on_party_id": t.blocked_waiting_on_party_id,
                          "since": t.blocked_since} for t in blockers],
            "needs_attention": needs_attention,
            "wrap_note": wrap_note.payload.get("text") if wrap_note else None,
            "wrap_note_by": wrap_note.actor_user_id if wrap_note else None,
            # TODO(B, blocked on Lane A's decisions): decisions_and_policies,
            # pending_proposals_aged, corrections_first.
        }

    # -- P6 (à la carte) --------------------------------------------------

    def close_out(self, project_id: int) -> dict:
        """TODO(B, P6): SRF-4 — retrospective digest on project close (G41)."""
        raise NotImplementedError

    def onboarding_brief(self, user_id: int) -> dict:
        """TODO(B, P6): SRF-5 — filtered read: active work, decisions shaping it, blockers."""
        raise NotImplementedError

    def offboarding_sweep(self, user_id: int) -> dict:
        """TODO(B, P6): SRF-6 — everything the departing volunteer holds, before it's lost."""
        raise NotImplementedError
