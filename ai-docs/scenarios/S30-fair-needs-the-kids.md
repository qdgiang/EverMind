# S30 — The fair demo needs the kids ready (run 6b, vs rev 5)

> Hunt target: **the new org-level bucket vs the old dependency validator.** G47 (rev 5) created
> standing teams and `project_id = null` ongoing tasks; the dependency rules were written in
> rev 2 ("cross-project edges forbidden"). Fresh seam. Complexity ★★★★.

## Scenario

Tết season (P-2 active; education is a standing team, its tasks org-level per G47):

- P-2 task "Kids' demo booth at Tết fair" (events-P2, PIC khoa) genuinely depends on the
  org-level ongoing task "Scratch course — spring cohort" (standing education team, PIC tuan)
  reaching lesson 6 by fair week.
- linh decides it in the all-hands group: "booth chỉ chạy nếu lớp Scratch xong bài 6 trước
  10/2 — khoa theo sát với tuan nhé."

## Trace against rev 5

1. Extraction proposes the edge: predecessor = Scratch course (org-level, `project_id = null`),
   successor = demo booth (P-2). The validator checks "cross-project edges forbidden". Is
   null-project ↔ P-2 *cross-project*? **Undefined.** Strict reading (different project_id
   values ⇒ forbidden) rejects the single most legitimate dependency in the org — seasonal work
   standing on the programs that ARE the org. Loose reading admits it by accident, unspecified.
2. Suppose admitted: the machinery downstream mostly works — visibility carve-out shows tuan's
   task minimally to khoa ✓; escalation LCA(mai-standing, linh-P2-chain)… mai's standing team
   hangs under the coordinator like everything else, LCA = linh ✓; radar slack math is
   project-agnostic ✓. The *only* broken piece is the admission rule itself.
3. Edge probe — the original ban's purpose: two *seasonal* projects must not chain (P-1 closed
   tasks can't block P-2 — S22 confirmed the need is knowledge, not sequencing). That rationale
   never applied to standing programs; the rule just predates the bucket.

## What holds up ✅

Everything after admission: carve-out, LCA routing through the coordinator, slack lamps,
unblocked ping (tuan marks lesson 6 done → khoa pinged "you can start"), and the close-out
interaction (when P-2 closes, the edge dies with the successor; the standing task is untouched
— G47's detach semantics compose correctly here).

## Gap

### G51 — Dependency validation predates the org-level bucket (severity: MEDIUM — one rule,
### but it forbids the org's most natural dependency)
- **Fix (replace the ban with a matrix):**
  - seasonal ↔ **same** seasonal project: allowed (unchanged).
  - seasonal ↔ **org-level ongoing**: **allowed, both directions** — programs are shared
    infrastructure. Cross-boundary edges always route escalation through the coordinator
    (they span authority domains by construction).
  - seasonal ↔ **different** seasonal project: forbidden (unchanged — including closed ones).
  - org-level ↔ org-level: allowed.
  - Close-out already handles the lifecycle: edges die with their seasonal endpoint; standing
    endpoints are never dragged.

## Verdict

**Gap found (G51)** — a regression-shaped seam: rev 5 added a new kind of place for work to
live and one rev-2 validator never learned about it. Exactly the class of bug iteration exists
to catch; one rule table fixes it.
