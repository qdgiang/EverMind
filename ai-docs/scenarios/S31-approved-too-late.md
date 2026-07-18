# S31 — Approved too late: stale acts on moved targets (run 6c, vs rev 5)

> Hunt target: **time-of-check vs time-of-use.** Proposals wait days; the world moves under
> them. Also: what exactly locks when a task reaches a terminal state? Complexity ★★★★.

## Scenario

- 07-20, tuan proposes extending the worksheet task's end_date to 25/7 (pending, tagged mai).
- 07-21, mai **cancels** the whole worksheet task ("gộp vào bộ slide mới") — effective.
- 07-23, mai, clearing her queue on the phone, **approves** tuan's 20/7 extension without
  noticing it's the canceled task.
- Meanwhile the stall-map husk (merged in S17) still has a pending decoration proposal from
  before the merge; and khoa, unaware, posts `!progress T-worksheet doing` after the cancel.

## Trace against rev 5

1. **The stale approval:** rev 5's zombie sweep clears same-unit proposals when an effective
   decision lands — but the cancel was a *status*-facet decision; tuan's proposal is
   *end_date*-facet. Different unit → survives, correctly (it's not the same question). mai's
   approve then mints an **effective end_date decision on a canceled task**. Nothing checks
   target state at approval time. Nonsense-but-recorded; worse on a **merged** husk, where the
   pre-merge proposal writes ops onto a redirect shell.
2. **The update after cancel:** khoa's `!progress doing` — he's a PIC, update lane auto-applies…
   rev 5 says cancel/revive are decision-only, but nothing **locks the update lane** on a
   canceled task. Fold order by ts ⇒ the later update's status write competes with the cancel.
   A member's marker just un-canceled (in effect) an authority's decision — the hierarchy rule
   breached through the side door.
3. **Reverse probe:** proposal to cancel pends while the PIC marks the task done. Approving
   cancel-of-a-done-task is at least a *conscious* act — but the approver sees the proposal
   text, not the task's current state. Every approval is made against a stale snapshot.

## What holds up ✅

The zombie sweep's unit-scoping is *right* (different facets are different questions); merge's
redirect exists; and because everything is append-only, none of these mistakes destroys
history — they just record nonsense that must then be vetoed (G17 resurrection works).
Prevention is missing, not recovery.

## Gap

### G52 — Terminal-state locking + approval-time revalidation (severity: MEDIUM-HIGH — the
### side door undermines the hierarchy rule itself)
- **Fix:**
  - **Terminal states lock the lanes:** on `canceled` and `merged` tasks, the update lane
    accepts **notes only** (khoa's `!progress` gets a bot reply: "task was canceled by mai on
    21/7 — reopen needs a lead decision"); status changes require a decision (`revive`), and
    ops-bearing decisions on a `merged` husk are auto-redirected to the survivor.
  - **Approval-time revalidation:** approving a proposal re-checks its targets *now*: target
    canceled → approval blocked with context ("task canceled 21/7 — approve anyway as revive +
    change, or dismiss?"); target merged → offer one-tap redirect of the ops to the survivor;
    target's same-unit value changed since proposal → show the diff before confirming. The
    approver acts on the present, not on a 3-day-old snapshot.
  - Proposal cards (bot + dashboard) always render **current target state** alongside the
    proposed change.

## Verdict

**Gap found (G52).** Rev 5 sequenced writes correctly but let *deferred human acts* land
without re-reading the world. One revalidation hook and one lane-lock close both doors.
