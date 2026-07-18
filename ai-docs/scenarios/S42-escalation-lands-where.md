# S42 — The escalation with no mailbox (run 8d, adversarial, vs rev 8)

> Adversarial target: **cross-boundary escalation's delivery address.** G51 says campaign↔program
> edges "route escalation through the coordinator" — through, but *to where*? One group ↔ one
> project makes the question sharp: there is no shared room. Complexity ★★★.

## Scenario

TT campaign task "Tiết mục văn nghệ" (khoa, PIC, trungthu group) depends on Classes task "Tập
tiết mục" (tuan, PIC, classes group). Rehearsals slip; day 3 arrives: escalate to both PICs +
the coordinator (linh). khoa is only in the trungthu group; tuan only in the classes group;
there is no all-hands group mapped in this seed.

## Trace against rev 8

1. Radar computes the at-risk lamp fine and knows the recipients. Then: **post where?** The
   rules say team-task pings go to the task's team group — but this is ONE escalation about TWO
   tasks in two groups. Options all unspecified: post in one group (the other PIC never sees
   it), post identical text in both (leaks upstream detail past the visibility carve-out?),
   DM the coordinator (no such lane defined).
2. Also probed, **held:** the union-graph DAG check — attempting the reverse edge (văn nghệ →
   tập tiết mục) is rejected with the cycle path, cross-project edges included ✓. Carve-out
   fields (title/status/end/owning team only) are exactly what the downstream group may see ✓.

## Verdict — FIX (cheap: one routing rule)

### G63 — Cross-boundary escalations need a defined delivery rule (severity: MEDIUM,
### fix cost: two sentences)
Escalation for a cross-boundary edge posts **one message per endpoint group**, each rendering
only *its own task's* side plus the other side's carve-out projection ("chờ: Tập tiết mục —
Classes, hạn 20/9"), tagging that group's PIC; the **coordinator is tagged in both**. If an
all-hands group is mapped, a combined copy goes there instead of duplicating coordinator tags.
No DM lane, no new visibility. **Fixed in rev 9.**
