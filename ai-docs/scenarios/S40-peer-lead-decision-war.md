# S40 — Two equal leads, one photographer (run 8b, adversarial, vs rev 8)

> Adversarial target: **the rank gate's `≥`.** Equal rank passes supersession — two peer leads
> can lawfully overwrite each other forever on any unit both may decide. Complexity ★★★.

## Scenario

A campaign with two teams and two rank-2 leads (the design allows it even if the demo seed has
one). Team-less project-level task "book photographer": G48 gives *any* lead of the project
authority. Lead A decides "chụp bởi studio X" (effective). Lead B — sincerely, not maliciously
— supersedes with "studio Y rẻ hơn" (rank 2 ≥ rank 2: gate passes, legal). A supersedes back
with X. Three days, five effective decisions, one photographer still unbooked.

## Trace against rev 8

1. Every write is **individually lawful**: same-unit supersession, rank gate satisfied, links
   and receipts perfect. The append-only history records a beautiful, useless rally.
2. The `contested` lamp (G55) watches **status flips by task_updates** — decision-level churn
   on a facet is a different table; nothing counts it. The digest lists each new effective
   decision (with receipts) but flags no pattern; the coordinator learns of the war only by
   reading closely or being tagged by an exhausted lead.
3. Peer-*proposal* ties are already handled (incomparable/equal ranks on a **held** second
   write → both leads tagged) — but that rule fires only when writes collide in flight. Spaced
   by days, each supersession is just… next.

## Verdict — ACCEPT (settled #15)

### G61 — No decision-churn detection between equal ranks (severity: LOW, likelihood: niche)
- **Why accepted:** requires ≥2 same-rank leads sharing a decidable unit AND sustained genuine
  disagreement — rare in a 10-person NPO, and *visible* even without detection: every flip is
  announced with receipts (G20 symmetry), the digest lists the dueling decisions side by side,
  and the coordinator (supersession apex) can end it with one decision at any moment. A churn
  detector (K same-unit supersessions by ≥2 equal-rank makers in T days → coordinator nudge)
  is easy to *describe* but adds another tuned threshold + config + notification lane for a
  case the org's own eyes catch.
- **Workaround on record:** coordinator supersession + the digest's decision list. Revisit
  post-hackathon if real usage shows peer churn (the query is one GROUP BY when needed).
