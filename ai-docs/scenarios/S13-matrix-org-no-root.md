# S13 — khoa is on two teams and nobody is the boss: the org chart vs the schema

> Verifies: whether `users {role, manager_id?, team_id?}` can even *represent* the synthetic
> cast — settled decision #7 says the corpus IS the org. Cast/canon: `data/` corpus personas.
> Gaps G36–G37. Complexity: ★★★★★ (structural).

## Grounding (answer key: personas)

- **Multi-team members:** khoa (events **+** education), thao (education **+** comms), minh
  (events **+** comms) — 3 of 10 personas. The answer key stores `teams: []`, plural.
- **No root:** three leads (linh/events, mai/education, phuong/comms) and **no director above
  them**. The transcript shows linh *chairing* the all-hands and holding org-wide powers (TD2:
  budget overrun "requires her sign-off") — a de-facto coordinator, never a declared one.
- Name collision warning: corpus `an` = comms member. S1–S5's fictional "An (Giám đốc)" is
  unrelated; corpus cast is authoritative from here on.

## Trace — try to write the Phase-0 seed file

1. `users.team_id` is a **single** nullable column. khoa's row cannot be written without either
   dropping a membership (then education-window candidates exclude him, his education tasks
   can't count toward his load, and `can_decide` mis-scopes) or duplicating the user (two khoa
   rows → split identity, double telegram mapping, double load). **The seed file for the actual
   demo cast is unbuildable as schema'd** (G36).
2. `manager_id` chain: mai → **?**. With no root, three disjoint trees. Consequences, all live:
   - **S4's escalation:** LCA(events, comms) = **undefined** — the cross-team slip in S10 (comms
     announcement blocked on events' permit) has no escalation target.
   - **S3-G10's rank gate:** rank(linh) vs rank(phuong) is **incomparable** (partial order across
     trees). If phuong's decision touched a shared task after linh's, the supersession gate can
     neither pass nor fail — it has no answer.
   - Two peer leads deciding differently about a shared workstream (the t-shirt task spans
     events+comms, S6-G23) → two effective same-facet decisions, no tiebreaker, no escalatee.
3. **Role strings:** "volunteer coordinator", "Python teacher" — the authority ladder (director >
   lead > member) must be *derived*; nothing in the schema declares which roles outrank which.

## What holds up ✅

- `manager_id` as adjacency is the right primitive — the failure is cardinality (one team) and
  a missing root, not the graph model.
- Role-at-time snapshots stay correct regardless of how the ladder is repaired.
- Load computation is per-user over tasks, so once memberships are fixed, khoa's cross-team load
  aggregates correctly with zero extra work — the overload design was accidentally matrix-ready.

## Gaps

### G36 — Multi-team membership: `users.team_id` cannot hold the actual cast (severity: HIGH,
### blocks Phase 0)
- **Fix:** `user_teams {user_id, team_id, role_in_team}` join (answer key's `teams:[]` maps 1:1);
  drop `users.team_id`. `can_decide` checks the manager chain against *any* owning team of the
  task; linkage candidates for a group include tasks of that group's team as before (membership
  doesn't change candidate scoping — S6-G23 already moved that to project scope). Load spans all
  memberships natively.

### G37 — No root: escalation and rank comparison are partial functions (severity: HIGH)
- **Expected (the data itself):** the transcript's TD2 gives linh org-wide sign-off power — the
  corpus *behaves* as if a coordinator exists without declaring one.
- **Fix, two options:**
  1. **Declare the root (recommended, and corpus-faithful):** seed `linh` as coordinator
     (manager of mai and phuong; events lead as a second hat via `user_teams`). LCA is total,
     ranks are comparable, TD2's sign-off rule matches her modeled power. One seed-file line.
  2. **Rootless fallback rules:** if LCA(a,b) is undefined → escalate to *all* leads of the
     involved teams in a shared/all-hands group; if ranks are incomparable → the later decision
     is born `proposed`, tagged to both leads (peer-conflict = explicit human tiebreak, never
     silent last-write-wins).
  Build **both**: option 1 for the demo, option 2 as the general rule so the model doesn't
  *require* every real org to have a root (many NPOs genuinely don't).
- Also: a tiny `role_rank` map (coordinator=3, lead=2, member=1) in the seed file makes the
  ladder explicit instead of string-derived.

## Verdict

Settled decision #7 ("the corpus is the org") is currently **unsatisfiable**: the schema cannot
express 3 of 10 personas or any usable ladder between the leads. Both fixes are seed-file-plus-
join-table cheap, but they gate everything downstream — G36/G37 must land before the Phase-0
seed, or the persona switcher, authority gates, and escalation routing all sit on a fictional
org rather than the one the demo replays.
