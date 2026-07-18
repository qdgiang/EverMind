# S39 — The merge that ate itself (run 8a, adversarial, vs rev 8)

> Adversarial target: **compose two fixed features until they contradict** — merge (G43) under
> dependency edges (G51). Complexity ★★★.

## Scenario

Duplicate lantern tasks exist (probabilistic linkage guarantees occasional dupes): T2 "Đặt lồng
đèn" and T2' "đặt đèn trang trí" (born from a poster thread). Before anyone notices, someone
records "trang trí phải chờ đèn về" twice: edge **T2' → T4** (decor), and — because a helper
"linked the duplicates" the only way the model allows — edge **T2 → T2'**. Then a lead merges:
survivor T2 absorbs T2'.

## Trace against rev 8

1. Merge transaction: "dependencies re-point (deps deduped)". T2'→T4 re-points to **T2→T4** —
   already exists? deduped ✓. The T2→T2' edge re-points to… **T2→T2. A self-loop.**
2. "Deduped" does not mean "self-loops dropped". A self-edge makes the blocked lamp read
   *T2 waits for T2*: permanently blocked by itself, radar pinging minh to finish the task so
   he can start it. The DAG cycle-check runs **at edge write time** — the loop was created by
   the *merge*, which never re-runs the check.
3. Everything else in the merge held (history union, per-unit resolution, assignments).

## Verdict — FIX (cheap: one clause)

### G60 — Merge must drop pair-internal edges and re-run the cycle check (severity: LOW-MED,
### fix cost: trivial)
Merge transaction addendum: edges **between the merged pair are dropped** (they were identity
confusion, not sequencing); after re-pointing, the DAG check re-runs over the survivor's edges
— any cycle aborts the merge with the path shown (same UX as edge writes). One sentence, no new
machinery. **Fixed in rev 9.**
