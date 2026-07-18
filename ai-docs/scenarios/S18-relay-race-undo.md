# S18 — The relayed decision, the race, and the accidental done (run 2a, vs rev 3)

> Hunt targets: relayed authority, approver silence, concurrent same-unit writes from two group
> flushes, misquoted relays, undoing a wrong progress update. Complexity ★★★★.

## Scenario

- 07-20, mai is sick. tuan in `aiv-education`: "cô mai nhắn nhờ mình post: chốt dời showcase
  sang 16/8 nhé." mai is offline for 2 days.
- Same afternoon, `aiv-events` flush and `aiv-education` flush both process messages touching
  the shared "kids' fair demo" task — linh set `attr:duration = 20 phút` in events chat; khoa
  wrote "demo chắc 15 phút thôi" in education chat.
- 07-21, tuan fat-fingers `!progress T-demo done` (meant the worksheet task), notices, fixes.

## Trace against rev 3

1. **Relay lane:** claimed maker (mai) ∉ cited authors → born `proposed`, tagged @mai,
   announced "📋 Proposed — awaiting @mai" (nobody mistakes it for effective). ts = the claimed
   decision time if evidenced, else the relay's ts; `recorded_at` = now. 48h later the nudge
   fires; the digest lists it under pending. mai returns, taps 👍 → `approval_via=self_confirm`,
   effective. **Misquote variant:** mai instead replies "23/8 chứ!" → she rejects the proposal
   and posts her own (or edits via dashboard persona) — challenge/reject lane covers it; the
   wrong relay never touched the projection. ✅
2. **The race:** two flushes, same unit (T-demo, `attr:duration`). Effective-writes serialize
   per target: linh's lands first (`effective`). khoa's arrives → same-unit occupied → khoa is a
   member (rank 1 < linh's 3): **not** a peer tie — the rank gate holds it `proposed`, tagged to
   linh; sweep-on-effective doesn't fire (khoa's came second). linh taps reject ("20 phút, đã
   đo sân khấu"). Had the second writer been mai (lead, but not > linh)? rank(mai)=2 <
   rank(linh)=3 → same path. True peer tie (mai vs phuong) → hold + both tagged, per §Facets. ✅
3. **The undo:** `!progress T-demo done` — tuan is not a PIC of T-demo → not auto-applied; bot
   asks a PIC to confirm (update lanes). Had he been PIC: applies, then his correction
   (`!progress T-demo doing` + right task marked done) is just the next update — append-only
   streams need no undo machinery; the popup shows the stumble honestly. Lamps recompute; no
   digest ran in between (flush-before-read is digest-time, so the digest never saw the blip). ✅
4. **Detail probe — the relayed decision's window:** tuan's relay is one message in a window
   with unrelated chatter; extraction links it to the showcase task via candidates; the
   supersession suspicion against the standing showcase date raises a suggestion that resolves
   only when mai confirms (a proposed decision can carry a pending supersedes-suggestion —
   resolved at effective-time by the normal transaction). ✅ (rev 3's lifecycle already orders
   suggestion-resolution at effective-write, not extraction time.)

## Hunted, found held

Relay misquote · approver silence (nudge + digest) · proposed-decision visibility · serialized
same-unit writes · rank-gate vs peer-tie routing · marker mis-fire by non-PIC · self-correction
without undo machinery · supersession suggestions on not-yet-effective decisions.

## Verdict

**Run 2a: no gaps.** Every beat resolved by rev 3 rules as written, with no rule-stretching.
