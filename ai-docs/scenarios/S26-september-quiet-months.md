# S26 — September: the classes that outlive their project (probe run 5c, vs rev 4)

> Hunt target: the seam between **G38 (one demo project, `kind=ongoing`) and G41 (close-out)**
> that S16 and S22 each probed alone but never together: what happens to a *program* in the
> months between two seasonal projects. Complexity ★★★★★.

## Scenario

08-15: P-1 (fair) reaches `closed` — close-out done, retro archived. The weekend classes
**continue every Sunday**: `aiv-education` keeps chatting, tuan runs Python, D4's Sunday-14:00
policy still governs, the projector blocker (B3) is still open. No new project exists until
Tết kickoff in December (S22).

## Trace against rev 4

1. **Close-out hits the class tasks.** The sweep proposes done/canceled/**migrate to ongoing**
   for open tasks. "Migrate" sets `kind=ongoing`… but the task keeps `project_id = P-1`, and
   P-1 is now `closed` — closed projects **leave active views**. The classes program, B3, and
   the weekly staffing tasks all sink with the ship. mai's team is fully operational in a
   system that just archived them.
2. **The team itself dies:** `teams.project_id = P-1`. When S22's new season re-seeds teams for
   P-2, "education" is a *new row* — so D4 (a **team-scoped policy** attached to P-1's
   education team) doesn't govern the new team; the policy trail fractures at every season
   boundary even though the program never blinked.
3. **The group mapping dangles:** `aiv-education` maps to (P-1, education-P1). From 08-15 to
   December there is no live project to remap it to. Windows keep firing (people keep
   chatting); candidates = "the project's open tasks" of a closed project. Undefined-to-wrong.
4. Root cause: G38's demo shortcut parked programs *inside* the seasonal project and G41 then
   closed the project. Each was locally right; together they orphan everything ongoing.

## What holds up ✅

- The close-out sweep itself (S16) and season succession (S22) still work for genuinely
  seasonal work (events/comms).
- Policy scoping to *teams* was the right instinct — it fails only because teams were chained
  to projects.
- The fix below is the minimal slice of the already-roadmapped "project-as-optional-scope" —
  the design predicted its own patch.

## Gap

### G47 — Ongoing work has no home outside a project: standing teams + org-level tasks
### (severity: HIGH — structural leftover of G38×G41)
- **Fix:**
  - `teams.project_id` becomes **nullable**: null = **standing team** (education), set =
    seasonal team (events-P2). Standing teams persist across seasons; their policies (D4),
    blockers, and membership never fracture.
  - `tasks.project_id` becomes **nullable for `kind=ongoing`**: null = org-level ongoing bucket.
    Close-out's "migrate to ongoing" now means: set kind=ongoing AND detach to project_id=null
    (or attach to the successor project if one exists and the lead says so).
  - `chat_groups` map to a **team** (standing or seasonal); the project is derived from the
    team when seasonal, null when standing. `aiv-education` → standing education team, valid in
    August and December alike; candidates = the team's open tasks (+ project's, when the team
    is seasonal). One-group-one-project survives as: a group serves at most one *seasonal*
    project at a time.
  - Digest/radar key on **team** (they already do); org-level ongoing tasks ride their standing
    team's digest. Defaulting: org-level tasks never end-date-default (nothing to default from)
    — warning-only, matching the closing-project amendment.
  - Seed impact: education = standing; events, comms = seasonal under P-1. (Corpus-faithful:
    the classes predate and outlive the fair.)

## Verdict

**Gap found (G47).** The demo shortcut was load-bearing; this pulls exactly one plank of the
honest model forward — nullable homes for standing work — and every prior mechanism (close-out,
succession, policies, digests) slots onto it unchanged.
