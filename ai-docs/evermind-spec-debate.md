# EverMind spec debate catalog

> Status: working document for GitHub Issues and merge-request discussion.
> This document does not override `design-v2.md`. A decision moves into the product spec only
> after explicit approval and corresponding scenario updates.

## Product model used by this debate

EverMind is a project-scoped, authority-aware event ledger. Telegram, Discord, uploaded files,
and the dashboard are input surfaces for the same domain model. Human authority determines what
becomes effective; tasks and dashboard resources are current projections. Every write keeps an
auditable event trail and material changes are announced back to the relevant group.

## Status legend

| Status | Meaning |
|---|---|
| `SETTLED` | Approved direction; the main spec still needs to absorb it. |
| `PREFERRED` | Current preferred option; important details remain open. |
| `OPEN` | Preserve alternatives and debate before changing the spec. |
| `ACCEPTED` | Known gap consciously deferred with a workaround. |
| `IMPLEMENTATION GAP` | Spec direction is known but contracts/tests do not implement it. |

## Settled decisions from the current debate

MR-ready correction body: [SPEC D1–D8 — Settled corrections for EverMind rev 10](debates/SPEC-D1-D8-settled-corrections.md).

| ID | Status | Decision |
|---|---|---|
| D1 | `SETTLED` | A group belongs to one project at a time through temporal bindings. A new-season cutover archives the old project; it does not hard-delete history. |
| D2 | `SETTLED` | A decision has a mutable current snapshot backed by immutable decision events/revisions. Material alternatives still supersede; amendments preserve the decision identity and audit trail. |
| D3 | `SETTLED` | The dashboard is a write surface. A dashboard edit is a domain command, not a direct projection update or a fake chat message. |
| D4 | `SETTLED` | `project_type: campaign|program` is explicit and independent of optional `end_date`. Program dates do not trigger campaign defaulting or automatic close. |
| D5 | `SETTLED` | Platform adapters map platform identities to an internal user. Identity keys must include connector/account or workspace scope when the platform requires it. |
| D6 | `SETTLED` | Approval authority basis and approval method are separate. Reply, reaction, dashboard, marker, and API are methods; direct authority, delegation, self-confirm, and multi-party rules are bases/requirements. |
| D7 | `SETTLED` | `data-v2` requires executable fixture, domain-scenario, and extraction-evaluation tests. |
| D8 | `SETTLED` | Read access is project-scoped by default. Project members can read all project resources; roles constrain writes. Raw evidence remains source-scoped. |
| D9 | `SETTLED` | Use bounded autonomy. A PIC may append notes/evidence and update progress, including `done`; shared/material facets require authority approval. |
| D10 | `SETTLED` | PIC handoff is two-key: the incoming PIC accepts and the lead/acting lead approves. Consent and authority are distinct events. |
| D11 | `SETTLED` | Project-wide changes require the project owner/coordinator. A team lead may propose; an acting coordinator is the fallback. Team-only policy remains under that team lead. |

## Issue catalog

| Issue | Priority | Status | Problem and proposed direction |
|---|---:|---|---|
| [EVM-001 Dashboard authentication](debates/EVM-001-dashboard-authentication.md) | P0 | `OPEN` | A write dashboard cannot use an unrestricted persona switcher. Keep judge/demo browsing read-only and require an authenticated session for writes. |
| [EVM-002 Marker double materialization](debates/EVM-002-marker-double-materialization.md) | P0 | `OPEN` | Marker messages also enter extraction windows. Materialize markers once, keep them as context, label them `already_materialized`, and deduplicate by source message + command index + kind/facet. |
| [EVM-003 Multi-operation decisions](debates/EVM-003-multi-operation-decisions.md) | P0 | `OPEN` | Split heterogeneous operations into a linked decision bundle; validate and commit a homogeneous all-or-nothing decision atomically. |
| [EVM-004 Overlapping exception windows](debates/EVM-004-overlapping-effect-windows.md) | P0 | `OPEN` | Conflicting effective exceptions on one facet cannot silently overlap. Hold the later proposal until its window is adjusted or it explicitly replaces the existing exception. |
| [EVM-005 Authority changes while pending](debates/EVM-005-authority-changes-while-pending.md) | P0 | `OPEN` | Re-check authority at action time, snapshot it in events, reroute pending work after org changes, and turn approval edit/removal into a challenge/correction. |
| [EVM-006 Canceled dependency predecessor](debates/EVM-006-canceled-dependency-predecessor.md) | P0 | `OPEN` | `done` satisfies; `canceled` produces `needs_rewire` and never “unblocked”; merge redirects; a lead explicitly removes an irrelevant edge. |
| [EVM-007 Q&A truth states and access](debates/EVM-007-qa-truth-and-access.md) | P0 | `OPEN` | Answer from effective state; label exceptions/proposals/challenges/history and filter permissions before retrieval. |
| [EVM-008 v1/v2 contract drift](debates/EVM-008-v1-v2-contract-drift.md) | P0 | `IMPLEMENTATION GAP` | Build a matrix from spec to domain schema, SQL, fixture, API, and tests. Ensure v2 tests cannot accidentally keep reading `data/`. |
| [EVM-009 Temporal group cutover](debates/EVM-009-temporal-group-cutover.md) | P1 | `OPEN` | Flush before atomic cutover, route late delivery by event time, constrain archive replies, and require import project scope. |
| [EVM-010 Transactional outbox](debates/EVM-010-transactional-outbox.md) | P1 | `OPEN` | Persist domain event and outbox atomically; retry delivery idempotently; register the platform message only after successful send. |
| [EVM-011 File-ingestion trust boundary](debates/EVM-011-file-ingestion-trust-boundary.md) | P0/P1 | `OPEN` | Verify MIME/magic and limits, reject encrypted files, never run macros, treat content as untrusted, version re-uploads, and produce granular citations. |
| [EVM-012 Late-event ordering](debates/EVM-012-late-event-ordering.md) | P1 | `OPEN` | Use valid causality, then `event_ts → recorded_at → stable_event_id`; invalid chronology goes to triage and late history cannot rewind present. |
| [EVM-013 Signal-ledger identity](debates/EVM-013-signal-ledger-identity.md) | P1 | `OPEN` | Key by project/task/party/topic, confirm first party match, audit merge/split, and require PIC/authority to resolve human blockers. |
| [EVM-014 Task split representation](debates/EVM-014-task-split-representation.md) | P1 | `OPEN` | Use nullable `parent_task_id` if split remains in MVP; otherwise defer one-tap split. |
| [EVM-015 Evidence retention and deletion](debates/EVM-015-evidence-retention-and-deletion.md) | P0 | `OPEN` | Define raw retention, tombstone/redaction, cached-copy access, and a `source unavailable/redacted` citation state. |
| [EVM-016 “Zero new habits” claim](debates/EVM-016-zero-new-habits-claim.md) | P2 | `OPEN` | Replace with “No new reporting destination for members; a lightweight exception-review loop for leads.” |
| [EVM-017 Overload and surveillance](debates/EVM-017-overload-and-surveillance.md) | P2 | `OPEN` | Show explainable workload risk, allow input correction, avoid rankings, and aggregate inaccessible cross-project details. |
| [EVM-018 Accepted G61/G64 gaps](debates/EVM-018-accepted-gap-triggers.md) | P2 | `ACCEPTED` | Keep gaps deferred with named workarounds, observable revisit triggers, and a manual query/runbook. |
| [EVM-019 Proposal authority and approval ledger](debates/EVM-019-proposal-authority-and-approval-ledger.md) | P0 | `PREFERRED` | Bounded autonomy and the authority matrix are approved. Exact approval-ledger schema, multi-domain requirements, and optional completion-review policy remain to be specified. |
| [EVM-020 Archive knowledge publication](debates/EVM-020-archive-knowledge-publication.md) | P0 | `PREFERRED` | Preserve all three access options. Current preference is a curated publication bundle reviewed by the project owner and approved by the coordinator. |
| [EVM-021 Concurrent dashboard/chat writes](debates/EVM-021-concurrent-dashboard-chat-writes.md) | P0 | `OPEN` | Dashboard commands carry expected resource version and command ID. A stale write shows a diff and requires reconfirmation rather than overwriting chat-originated state. |
| [EVM-022 Proposal capture and liveness](debates/EVM-022-proposal-capture-and-liveness.md) | P1 | `OPEN` | Debate receipt guarantees, missed extraction, reminders, acting-authority rerouting, escalation, and stale proposals. No silent approval. |

## Suggested resolution order

1. Resolve P0 semantics and update affected scenarios.
2. Write `design-v2` revision 10 with only settled decisions.
3. Rebuild v2 contracts and executable `data-v2` acceptance tests.
4. Implement connectors, file ingestion, notifications, and dashboard writes.
5. Revisit P2 product-risk and accepted-gap triggers using real usage evidence.

## GitHub workflow

Each linked debate file is intentionally issue-ready: problem, invariants, options, preferred
direction, edge cases, acceptance scenarios, and a decision checklist. When an issue is resolved,
record the chosen option and update this catalog before changing `design-v2.md`.
