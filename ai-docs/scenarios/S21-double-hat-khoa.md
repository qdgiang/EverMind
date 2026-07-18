# S21 — khoa wears two hats and both teams pull (run 3b, vs rev 4)

> Hunt targets: matrix membership under load, cross-team tug-of-war over a shared person,
> member-initiated reassignment, peer-lead tie with a root present. Complexity ★★★★★.

## Scenario (fair-minus-two-weeks)

- khoa (events + education) holds: volunteer roster (events, due 07-25), stall assignments
  (events, due 07-30), Sunday class staffing (education, weekly), buddy pairing for 2 newcomers
  (education). linh drops "khoa lo thêm vụ parking volunteers nhé" (urgent) on 07-21.
- khoa, drowning: "mình chuyển buddy pairing cho tuan được ko?"
- mai and phuong simultaneously decide different owners for thao's fair-photos task (education
  vs comms hats) — a true peer tie.

## Trace against rev 4

1. **Load across hats:** per-day concurrent load sums over ALL khoa's teams via `user_teams` —
   5 windows overlapping the same week, one urgent ⇒ overload threshold crossed. ✅
2. **The urgent add in chat:** linh assigns (rank 3, effective immediately, `assignment add` —
   bare "lo thêm" = add, Minh-style silent replacement impossible). Overload check runs
   post-hoc → warning reply tags linh + khoa ("khoa now has 5 active, 3 due this week"); linh
   doesn't retract in X hours → acceptance noted on the decision. The risk is citable when the
   roster slips later. ✅
3. **Member reassigning his own task:** khoa's "chuyển cho tuan" is an `assignment set/remove+add`
   on a task he PICs — assignment is a *decision* facet, khoa is rank 1 → born `proposed`,
   tagged to… which authority? The task is education-scoped → mai (its team's lead). mai 👍 →
   effective (`approval_via: authority`). Correct friction: handing off work is visible to the
   lead, not silent. (Had mai pre-said "cứ đưa tuan" in-thread → delegation lane, instant.) ✅
4. **The peer tie:** mai's and phuong's same-unit (`assignment set` on fair-photos) effective
   writes serialize; the second is held `proposed`; ranks equal (2 = 2) and **LCA exists: linh**
   (rev 4 seed) → both leads + linh tagged; linh tiebreaks with one decision (rank 3 supersedes
   whichever landed). The rootless fallback never triggers because the seed has a root — but the
   trace confirms the partial-order logic routes rather than crashes. ✅
5. **Probe — thao's own preference:** thao (member, both teams) replies "em muốn làm bên comms."
   Consistent-with-nothing-effective-yet → it's an opinion on a contested unit: extraction files
   it as a note on the task (execution-zone rule doesn't apply — it's not her PIC'd task yet —
   so: `ask/parked`-grade signal at most). Her voice lands in the reasoning trail via citation
   when linh decides; she can't be silently overridden *or* silently deciding. ✅
6. **Probe — load double-count:** the fair-photos task is `task_teams` = {education, comms}
   during the dispute; khoa uninvolved, thao's load counts the task **once** (load is per-task
   per-person, not per-team-membership). No inflation. ✅

## Hunted, found held

Cross-hat load aggregation · post-hoc chat overload with logged acceptance · additive-by-default
assignment · member handoff friction routed to the right lead · delegation shortcut · serialized
peer tie with root tiebreak · contested-unit opinions as citable notes · no per-team load
double-counting.

## Verdict

**Run 3b: no gaps.**

---

**Iteration run 3 result: S20 clean + S21 clean → consecutive-clean count = 1. One more clean
run required.**
