# EVM-022 — Proposal capture and liveness

> Priority: P1
>
> Status: `OPEN` — alternatives are intentionally preserved for GitHub debate.

## Problem

A safe authority model still fails operationally when EverMind misses a member's proposal or the
required lead forgets it. Silence must not change shared truth, but a permanently pending queue
also recreates the coordination bottleneck EverMind is meant to remove.

This issue is separate from EVM-019: EVM-019 decides who may approve and what becomes effective;
EVM-022 decides how a recognized proposal stays visible and eventually reaches a human decision.

## Proposed invariant: explicit receipt

A member should consider a proposal captured only after EverMind returns a receipt containing:

- Target resource or `UNLINKED` state.
- Current and proposed values when known.
- Required approver or unresolved routing state.
- An explicit statement that the projection has not changed.

No receipt means “not captured,” not “probably pending.” Deterministic fallbacks may include
`!propose`, reply to a task/bot card, and a dashboard proposal form.

## Reminder and escalation options

### Option A — Fixed SLA escalation

Notify the primary approver, remind after a fixed interval, then escalate to acting authority.
Simple and measurable, but it may interrupt active negotiation and create notification fatigue.

### Option B — Activity-aware escalation (`PROPOSED`)

Measure inactivity from `last_activity_at`; discussion or an amendment resets the reminder clock.
Reroute immediately when the approver is unavailable. Escalate only after sustained inactivity.
This is quieter but adds state and more timing scenarios.

### Option C — No automatic escalation

Keep pending proposals in the dashboard/digest and let humans pull from the queue. This is simple
but makes forgotten proposals likely and weakens the early-warning promise.

## Missed-capture options

- AI-only capture: least new habit, but no deterministic recovery.
- AI capture plus explicit fallback (`PROPOSED`): receipt makes failure visible; markers/forms
  recover important misses.
- Require explicit proposal commands: most deterministic, but contradicts ambient capture.

## Rules that hold across all options

- Silence never approves or rejects.
- A stale proposal cannot apply without current-state and current-authority revalidation.
- Duplicate proposals with the same target/op/value merge citations; different alternatives stay
  separate.
- A connector or extraction backlog is visible; unavailable capture is never presented as a quiet
  group.
- Acting authority must be explicitly delegated or higher in the authority chain, never an
  arbitrary backup member.
- If an acting authority resolves the proposal, the returning primary approver may challenge or
  supersede normally but cannot silently undo it.

## Edge cases to debate

- Lead reads a proposal in chat but never interacts with EverMind.
- Lead comments “đang xem” and the system must decide whether that resets the clock.
- Proposer amends the value after one approval in a multi-approval requirement.
- Proposal is extracted days late after the task has changed or completed.
- Bot is missing from the group when the proposal is written, then capture resumes.
- Primary and acting authority issue conflicting actions nearly simultaneously.
- Project closes or the task transfers while the proposal remains pending.

## Acceptance scenarios for the eventual resolution

- The proposer can unambiguously tell whether EverMind captured the request.
- A missed AI extraction has a deterministic recovery path.
- An ignored proposal remains non-effective but visible and attributable.
- Active negotiation does not produce misleading approval state.
- Rerouting and escalation never broaden authority.
- Late approval cannot overwrite a newer task version without an explicit diff and reconfirmation.

## Decisions required in the GitHub issue

- Choose fixed, activity-aware, or no automatic escalation.
- Choose reminder/escalation intervals and urgent overrides.
- Define what user activity resets a reminder clock.
- Decide whether `stale` is a status or a derived badge on `pending`.
- Decide how long unresolved `UNLINKED` proposals stay in triage.
