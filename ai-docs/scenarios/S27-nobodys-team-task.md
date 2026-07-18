# S27 — The photographer task that belongs to nobody's team (probe run 5d, vs rev 4)

> Hunt target: **team-less tasks.** The review explicitly allows null teams ("PIC / phòng ban
> đều có thể null"); rev 4 allows project-wide chat groups (`team_id` null). Follow a task born
> that way through every mechanism. Complexity ★★★.

## Scenario

In the project-wide all-hands group, linh: "cần book photographer cho fair, ai quen ai giới
thiệu nhé — mình tạo task này." A task is created with **no owning team** (correct: it's
project-level work). Later khoa proposes a photographer; linh assigns him; the task nearly
misses its date.

## Trace against rev 4

1. **Creation:** NEW_TASK in a project-wide group — rev 4: authority checked against "any team
   the actor leads" — linh passes (coordinator). Task created, `task_teams` empty. ✅
2. **Later decisions on it:** `can_decide(actor, task)` = "actor in the manager chain above ANY
   owning team of the task". **No owning team → the condition is vacuously false → nobody —
   including linh — can decide on this task ever again.** The authority function is a partial
   function and this input is outside its domain. (Reality: implementations would do something
   accidental here; the *design* is silent, which is worse.)
3. **Digest:** per-team digests query by owning team → a team-less task appears in **no digest,
   ever**. Its deadline approach, its blocked state, its completion — invisible in the product's
   main surface. The radar computes its lamps (per-task SQL, fine) but posts them "to the
   affected teams' groups" — there are none.
4. **Candidates:** fine — G23 made candidates project-wide, so extraction can link chatter to
   it. Discovery works; governance and reporting don't.
5. **Overload:** fine — load is per-user over tasks, teams irrelevant. khoa's load counts it. ✅

## What holds up ✅

Creation authority, linkage/candidates, load math, and the lamps themselves — the task computes
correctly everywhere except *who may govern it* and *where it reports*.

## Gap

### G48 — Team-less tasks: authority undefined, no digest home (severity: MEDIUM — narrow but
### a hard hole, and the review's own nullability rule guarantees these tasks exist)
- **Fix:**
  - **Authority:** a task with no owning team is **project-level** (or org-level if
    project-less per G47): `can_decide` = any lead of that project (rank ≥ 2 within it), with
    the coordinator as tiebreak/supersession apex; org-level → any standing-team lead or
    coordinator. One added clause, total function restored.
  - **Reporting home:** the digest gains a **"project-wide"** section — team-less tasks and
    project policies — appended to every team's digest (shared context, cheap) and posted in
    the all-hands group when one is mapped. Radar pings for team-less tasks go to the all-hands
    group (fallback: the coordinator).
  - Assignment nudge: a team-less task whose PICs all belong to one team gets a one-time
    suggestion to adopt that team (keeps the bucket small without forcing it).

## Verdict

**Gap found (G48).** Small surface, but the review's nullable-team rule plus rev 4's own
project-wide groups make these tasks routine — and today the design literally cannot govern or
report them.
