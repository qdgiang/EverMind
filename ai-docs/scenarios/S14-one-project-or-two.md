# S14 — Is AIV one project or two? The fair, the classes, and the project boundary

> Verifies: the review's project rules (projects fully separate; one group ↔ one project; every
> project has an end date; end-date defaulting) against the NPO the corpus actually depicts.
> Cast/canon: `data/` corpus. Gap G38. Complexity: ★★★★★ (structural).

## Grounding

The corpus contains **two workstreams with different shapes**:
- **Charity fair** — a classic *project*: hard end date (2026-08-02, locked in TD1), budget cap,
  countdown energy ("23 days to the fair", m0500).
- **Weekend classes** — an *ongoing program*: no end date, recurring rhythm (D3→D4 schedule
  changes), continues after the fair indefinitely.

And the channels are **per-team, not per-workstream**: `aiv-education` carries class business
*and* fair business (S-w28-education: "kids' fair-demo plan to be finalized"); khoa's volunteer
sheet serves both (it drives D4's Sunday move *and* fair staffing 26/30); minh's t-shirts are
fair work discussed in comms and events.

## Trace — both modelings fail a rule

**Option A — one project ("AIV Summer 2026", end 08-02):**
- Group mapping ✓ (each channel → the one project). Cross-workstream links ✓.
- **End-date defaulting breaks:** every class task without an end date auto-sets to 08-01
  (project end − 1 day) — *nonsense* for a program that runs past the fair. Worse, on 08-03 the
  project is "over" while half its tasks legitimately continue. The review's "all projects have
  end dates" assumption is simply false for programs.

**Option B — two projects (Fair, Classes):**
- End dates: Fair ✓; Classes has none → **violates "các dự án đều có end date"** outright.
- **Group exclusivity breaks:** `aiv-education` would serve both projects — the review's rule #1
  ("không có nhóm chat nào được sử dụng cho 2 project") is violated by the corpus's own reality;
  ingestion cannot route a message to a project by group alone.
- **Cross-project edges are forbidden**, but the fair *depends* on class-side assets (volunteer
  pool, kids' demo, the school relationship that got the gym free) — the ban severs real links.

Either way, a review rule collides with the review's own synthetic-world truth.

## What holds up ✅

- Teams as the routing unit is solid — every message DOES belong to exactly one team channel.
- The fair, taken alone, is a perfect fit for the project model (end date, cap, countdown) —
  the model isn't wrong, it's *incomplete*: it assumes all work is fair-shaped.

## Gaps

### G38 — The project layer assumes everything is a dated project; programs exist (severity:
### HIGH, blocks Phase-0 seed — the seed must pick a modeling)
- **Fix (demo, minimal):** one project, `end_date` **nullable** semantics split by task:
  - `tasks.kind: project|ongoing` (default `project`). End-date defaulting and the
    "end > project end" warning apply **only to `project` tasks**; `ongoing` tasks (classes,
    recurring ops) are exempt and excluded from fair-countdown lamps.
  - Extraction hint: recurring language ("hàng tuần", "mỗi chủ nhật") → `ongoing`.
  This keeps one group↔one project (rule intact), kills the nonsense defaults, and needs one
  column.
- **Fix (model, honest):** project becomes an optional *scoping* of tasks, not a partition of
  groups: `chat_groups → team` only; `tasks.project_id` nullable ("org-level/ongoing work").
  The review's exclusivity rule survives as a *constraint where projects are used*, not a claim
  about all work. Cross-workstream dependencies become ordinary in-org edges. Document this as
  the post-hackathon direction; don't build it in 48h.
- Also note: with Option A the "project end" of 08-02 gives the demo its natural climax
  (countdown lamps, D-day digest) — a staging argument, independent of correctness.

## Verdict

The review's project rules were written from a corporate delivery-project frame; the synthetic
NPO immediately produces work that frame can't hold (ongoing programs, shared channels, real
cross-workstream links). The one-column demo fix (`tasks.kind`) absorbs the collision; the
deeper fix (project as optional scope) is the honest model and should be in the roadmap slide,
because every real NPO — including the one in the problem statement — runs programs, not just
projects.
