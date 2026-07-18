# S41 — The provisional who claimed a task and vanished (run 8c, adversarial, vs rev 8)

> Adversarial target: **G44's pruning rule vs everything a provisional can accumulate.**
> Complexity ★★★.

## Scenario

Trang (provisional, never lead-confirmed) claims the unowned games-stall task — approved, she's
PIC. She files one proposal ("mua thêm bóng bay"), posts two progress notes… then goes silent
for three weeks (exams). G44: "quiet provisional users are pruned after N days without the
offboarding sweep."

## Trace against rev 8

1. **Prune as written:** her user row is removed/deactivated *without the sweep* — that clause
   existed to keep pruning cheap. But she now HOLDS things: a PIC-ship (the stall task silently
   loses its only owner — no reassignment proposal, because that's the sweep we skipped), a
   pending proposal (its author evaporates mid-queue), and progress notes whose actor must stay
   resolvable in the popup forever.
2. The idle lamp (G56) would eventually notice the orphaned task — days later, by accident,
   with no explanation attached. The approval queue shows a proposal from a ghost.
3. Adversarial side-probes that **held**: her `!decision` attempts stayed `proposed` (rank 1)
   with one coaching reply (G49); her ambiguous "ok" reply approved nothing and the pending
   announcement stayed visibly unchanged (G5) — the 👍/reply lanes remain available to ranked
   users only. Attribution of her past updates survives any pruning (append-only actors).

## Verdict — FIX (cheap: one guard clause)

### G62 — Pruning must be holdings-aware (severity: MEDIUM, fix cost: one condition)
Prune a quiet provisional **only if they hold nothing** (no PIC-ships, no pending proposals).
Otherwise: keep the user, flag to the team lead with a mini-sweep (one reassignment proposal
per held task, dismiss-or-adopt for the pending proposal) — i.e., route through the *existing*
offboarding machinery at provisional scale instead of around it. Historical actor references
are never deleted regardless (append-only). **Fixed in rev 9.**
