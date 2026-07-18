# S22 — Tết season: same groups, new project, old memory (run 4a, vs rev 4)

> Hunt targets: project succession — the NPO reuses its Telegram groups for the next campaign,
> people re-form teams, and last season's memory must stay reachable. Complexity ★★★★★.

## Scenario

Dec 2026: P-1 (fair) is `closed` (G41 flow ran in August). AIV spins up **P-2 "Tết Charity
Drive 2027"** (end 2027-02-14). Reality: **the same `aiv-events`/`aiv-comms` Telegram groups
keep chatting** — nobody makes new groups. mai sits Tết out; 8 new volunteers pour in; phuong
asks "/ask năm ngoái sao mình chọn gym Nguyen Du nhỉ?"; huong wants "danh sách sponsor năm
ngoái"; duc's first big task depends on "the layout doc from last year".

## Trace against rev 4

1. **Project succession = config ops (logged):** create P-2, new `teams` rows, re-seed
   `user_teams` (mai omitted — she simply isn't a P-2 member; her P-1 history and snapshots are
   untouched), **remap the existing chat_groups rows to P-2**. One-group-one-project holds *at
   any point in time*; the mapping is consulted at extraction time, so: new windows use P-2
   candidates; every P-1 record already carries its project permanently; citations are
   message-id links, unaffected by remapping. History cannot re-attribute. ✅
2. **Straggler P-1 chatter after remap** ("à quên, còn 2 áo fair chưa gửi"): links against P-2
   candidates → no match → UNLINKED → triage, where a human attaches it to the archived P-1
   task. Designed stance (precision over guessing) — expected behavior, not a gap. ✅
3. **The memory reach-back:** Q&A is not scoped to active projects — phuong's venue question
   answers from closed-P-1 decisions (D2 ⊃ D1) with citations; huong's sponsor list comes from
   **`parties`, which is global by design** — the sponsor/vendor knowledge survives project
   death with contact notes attached. This is the institutional-memory pitch working across a
   season boundary. ✅
4. **"Depends on last year's layout doc":** cross-project *edges* are forbidden — correctly:
   P-1 has no live tasks to depend on. The need is knowledge, not sequencing → served by Q&A /
   onboarding brief over the archive; duc's new task just cites the old record in its context.
   The ban costs nothing real here. ✅
5. **The new-volunteer wave:** 8 unknown senders → provisional users (G44), one batched confirm
   line per group to the P-2 leads; all 8 fully functional immediately. mai posting in the group
   despite not being a P-2 member: she's `active` but team-less in P-2 → her messages ingest,
   her assertions route like any non-member's (propose/confirm lanes) — graceful, no ghost
   authority (her old lead rank was per-P-1-team via `user_teams`, which she no longer holds).
   Role snapshots keep her P-1 decisions honest. ✅
6. **Probe — same-name policy across projects:** P-2 sets `attr:donation-method = Momo` (new
   treasurer's call). Policy units are per **scope-target** (P-2 ≠ P-1), so it does NOT
   supersede P-1's VietQR decision; Q&A about "now" answers Momo (P-2 effective), "last year"
   answers VietQR (P-1 archive). No cross-project supersession bleed. ✅

## Hunted, found held

Group remapping vs history attribution · straggler triage · Q&A over closed projects · global
parties as cross-season memory · cross-project dependency ban vs knowledge reuse · provisional
wave at scale · departed-from-project member posting · per-project policy unit isolation.

## Verdict

**Run 4a: no gaps.** Succession is config + archive semantics already in rev 4; nothing new
required.
