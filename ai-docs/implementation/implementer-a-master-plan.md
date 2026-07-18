# Implementer A Campaign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete every mandatory Implementer A deliverable from P0 through P6 plus A's
P7 hardening responsibilities on `feature/implementer-a`, ready for the user's final review.

**Architecture:** Build the write spine sequentially: org/database foundation, append-only
decision gateway, LLM-backed ingestion, human acts, A-owned API/UI, and cited knowledge.
Each phase is a separate branch and PR into the A integration branch; B dependencies are
verified through frozen contracts and test doubles rather than cross-module edits.

**Tech Stack:** Python 3.12+ · FastAPI · Pydantic 2 · SQLAlchemy 2 · Alembic · PostgreSQL
16 + pgvector · OpenAI-compatible DeepSeek API · pytest · Next.js 15 · React 19 · TypeScript
· Tailwind CSS · Docker Compose · GitHub CLI

## Global Constraints

- Follow `ai-docs/implementation/implementer-a-charter.md` in full.
- Current scaffold/contract baseline is main commit `79ba7e3`; synchronize newer main
  contracts at every phase boundary.
- Phase PRs target `feature/implementer-a`; only the final MR targets `main`.
- Never modify a B-owned module to satisfy an A test.
- Shared contracts are read-only inside phase PRs.
- Use real DeepSeek for LLM-path development and local blocking evaluation.
- `frontend_ref/` is the final visual design; A owns only DSH-4, DSH-6, and DSH-7.
- Open issues are outside implementation scope unless their resolution is merged into a
  canonical contract.
- Use TDD, keep commits under 700 changed lines, and include tests with each behavior.
- Do not delete a file without explicit permission for that exact target.

---

## Current baseline

The repository contains a merged scaffold, not a completed P0:

- Contracts and every backend module path exist.
- `backend/migrations/versions/0001_initial.py` creates metadata tables and installs a
  partial append-only trigger; it is already merged and will not be rewritten.
- `backend/evermind/org/seed.py` does not exist, while `make seed` calls it.
- `OrgService` exposes basic getters and unimplemented future-phase ports.
- The frontend shell builds, while A-owned decision and Q&A routes remain placeholders.
- Local `uv` is absent and is installed during the approved P0 preflight.
- Local frontend build was green on 2026-07-18; backend commands were not run locally because
  `uv` was absent.

## Campaign file map

| Area | Stable responsibility |
|---|---|
| `backend/evermind/org/` | Seed, identity, authority reads, provisional users, party reads |
| `backend/evermind/decisions/` | Append-only records, lifecycle, authority, command gateway, events |
| `backend/evermind/llm/` | Provider-neutral live JSON gateway, validation, retry, call records |
| `backend/evermind/ingestion/` | Markers, windows, hydration, extraction, linkage, arrival lane, eval |
| `backend/evermind/knowledge/` | Structured retrieval, truth-state filtering, cited Q&A, measured vector track |
| `backend/evermind/api/` | App assembly, persona scope, command front door, A routers |
| `frontend/app/decisions/` | DSH-4 decision and policy logs |
| `frontend/app/qa/` | DSH-6 cited Q&A |
| `frontend/components/decisions/` | DSH-7 proposal and command interactions |
| `frontend/lib/api-client.ts` | Shared typed command client and conflict outcomes |
| `backend/tests/` | A-owned L1/L2/L3/L4-contract coverage |
| `ai-docs/implementation/phases/` | One executable plan for the active phase |

## Gate protocol used by every phase

- [ ] Coordinator updates `feature/implementer-a` with current `main` contracts.
- [ ] Coordinator creates the named phase branch and isolated worktree.
- [ ] Implementer reads the charter, this plan, and the current executable phase brief.
- [ ] Implementer completes RED/GREEN/refactor cycles and freezes a candidate SHA.
- [ ] Reviewer specialist checks that SHA and reports blocking findings or `PASS`.
- [ ] Tester specialist runs the phase commands from that SHA and reports `PASS` or `FAIL`.
- [ ] Implementer resolves failures; reviewer and tester rerun against the new SHA.
- [ ] Coordinator records evidence and merges the phase PR with a merge commit into the A
  integration branch.
- [ ] Coordinator creates the next executable phase brief from the newly merged state.

## Phase sequence

### P0 — Foundation

**Branch:** `feat/a-p0-foundation`

**Produces:** a safe corrective migration after merged `0001`, a validated deterministic
org seed loader, and a verified backend foundation.

**Principal files:**

- Create `backend/migrations/versions/0002_p0_foundation_corrections.py`.
- Create focused seed schema, ID map, service, and CLI files under
  `backend/evermind/org/`.
- Modify only A-owned org/database model details required by the corrective migration.
- Add PostgreSQL-backed migration and seed tests under `backend/tests/p0/`.
- Correct stale executable fixture counts in A-touched documentation without changing the
  fixture or answer key.

**Exit:** clean database to head; existing `0001` database to head; corrected append-only
trigger; seed twice with stable IDs and counts; L0 plus P0 tests, lint, and import boundaries
green.

### P1 — Decision core and command gateway

**Branch:** `feat/a-p1-decisions`

**Produces:** DEC-1 through DEC-9, authority reads, one-effective-per-unit transactions,
command idempotency/version conflicts, domain-event append, and birth-side late ordering.

**Principal files:**

- Complete A-needed authority methods in `backend/evermind/org/service.py`.
- Add small focused files beneath `backend/evermind/decisions/` for facet units, authority,
  lifecycle transactions, command routing, and outcomes; keep `service.py` orchestration
  thin.
- Add A-owned L1 tests under `backend/tests/scenarios/` for decision lifecycle, policies,
  hierarchy, windows, proposal hygiene, ordering, multi-op behavior, write plumbing, and
  invariants.

**Consumes:** `contracts.commands`, `contracts.events`, the org read port, and B's published
task-state port shape through injection.

**Produces:** transactional `DomainEvent` rows and deterministic command outcomes used by B
projections.

**Exit:** all A-owned P1 scenario suites pass against PostgreSQL with no LLM or platform
calls; S3 apple-to-peach command trace produces the specified decision/event state.

### P2 — Ingestion spine and live extraction gate

**Branch:** `feat/a-p2-ingestion`

**Produces:** real DeepSeek gateway, marker grammar, transactional windows, context hydration,
validated extraction, linkage, provisional-user arrival, materialization deduplication, and
the live/recorded evaluation harness.

**Principal files:**

- Split `backend/evermind/llm/client.py` into focused configuration, result, retry, and JSON
  validation responsibilities as the implementation requires.
- Add focused marker, window, hydration, extraction-schema, linkage, materialization, and
  arrival files under `backend/evermind/ingestion/`.
- Add `backend/evermind/ingestion/eval.py` and report/recording support.
- Add prompt assets under `backend/evermind/ingestion/prompts/`; prompts remain owned by the
  caller, not the LLM gateway.
- Add L2 tests and score calculations under `backend/tests/eval/`.

**Consumes:** B's message-read service port via dependency injection and the A command
gateway.

**Produces:** typed commands, materialization outcomes, failed-window backlog state, recorded
LLM responses, and `eval-report.json`.

**Exit:** live batch-25 and batch-100 profiles meet every L2 threshold; a rerun creates no
duplicates; injected instructions inside evidence cannot alter the extraction schema or
system policy.

### P3 — Human acts and corroboration

**Branch:** `feat/a-p3-acts`

**Produces:** affirmation/negation replies, tracked reaction acts, grace reversal,
post-grace challenge, revision-at-act binding, approval revalidation, and corroboration
append behavior.

**Principal files:**

- Add focused act classification, revision binding, reaction lifecycle, and revalidation
  files under `backend/evermind/decisions/`.
- Extend ingestion extraction outputs for corroborations without emitting duplicate
  decisions.
- Implement A's transcript-upload event handler against B's seam through an injected port.
- Add S44–S46 and related cross-room/terminal tests under `backend/tests/scenarios/`.

**Exit:** act/evidence scenarios pass, prompt changes retain P2 live thresholds, and missing
B transcript integration is recorded only as an external integration item.

### P4 — API, decision UI, and command surfaces

**Branch:** `feat/a-p4-api-dashboard`

**Produces:** persona validation, command front door, org/decision read APIs, DSH-4 logs,
DSH-7 proposal forms, typed writes, idempotent retry, conflict diff, and receipts.

**Principal files:**

- Complete A-owned files under `backend/evermind/api/` and keep business rules in domain
  services.
- Add response/request models close to their A-owned routers.
- Complete `frontend/lib/api-client.ts` without changing B's shell.
- Replace the A-owned decision placeholder with components under
  `frontend/components/decisions/` and `frontend/app/decisions/`.
- Add proposal surfaces under the decision component boundary.
- Add L3 API tests and focused command-client tests.

**Consumes:** the B shell as-is and published read ports only.

**Produces:** stable A API responses and a typed command client that B UI may consume later.

**Exit:** L3 validation/persona/version tests pass; Next build and type checks pass; A-owned
views match `frontend_ref/` across desktop and responsive states with accessibility basics.

### P5 — Cited knowledge and Q&A

**Branch:** `feat/a-p5-knowledge`

**Produces:** structured-first retrieval, truth-state filtering, citation-completeness
enforcement, live cited answers, DSH-6, and A-owned hero contract coverage.

**Principal files:**

- Add focused retrieval, truth-state, citation, and answer composition files under
  `backend/evermind/knowledge/`.
- Complete the A-owned Q&A router.
- Replace the Q&A placeholder under `frontend/app/qa/` and add focused Q&A components.
- Add knowledge/API tests and A-owned L4 contract tests.

**Consumes:** structured decision state plus published task/signal/party read shapes through
injected ports.

**Produces:** answers whose lines are either cited or visibly dropped, with pending and
inactive truth states labeled rather than presented as current truth.

**Exit:** truth-state and citation tests pass; the three hero questions return the expected
fixture-grounded receipts; frontend build and visual checks pass.

### P6 — Measured retrieval extension

**Branch:** `feat/a-p6-retrieval`

**Produces:** a measured decision on whether pgvector improves real missed queries.

**Principal files:**

- Add a keyword/structured retrieval comparison report under A-owned evaluation output.
- If and only if the report identifies a fixture-grounded recall miss, add the smallest
  pgvector repository and migration inside `knowledge`, plus regression tests.
- If no miss exists, record the evidence and do not add LangChain/vector abstractions.

**Exit:** retrieval comparison is reproducible. Any vector implementation demonstrates a
measured improvement without reducing truth-state or citation correctness.

### P7 — A hardening and final evidence

**Branch:** `feat/a-p7-hardening`

**Produces:** a frozen A candidate, final live evaluation, trust-boundary review, A-owned
regression report, and final MR materials.

**Principal files:**

- Fix only A-owned findings from review and test specialists.
- Update `ai-docs/implementation/final-review-report.md` with phase PRs, commit SHAs,
  commands, results, live metrics, known limits, and integration-pending items.
- Update the project changelog with implementation commit SHAs and timestamps.

**Exit:** every A-owned test and gate passes; no credential or outbound path exists in A
code; schema/prompt changes are frozen after the final live evaluation; the final MR to
`main` is open and awaiting the user's review.

## External dependencies that do not fail A ownership

- Live-eval GitHub workflow wiring belongs to B; A sets the secret and runs the gate locally.
- Full L4 with real connectors/tasks/signals/surfacing requires B's branch and is not an A
  merge responsibility.
- A records exact contract-tested behavior and any missing real integration in the final
  report without modifying B code.

## Final handoff

When all phase PRs have merged into `feature/implementer-a`, the coordinator:

- [ ] Synchronizes current `main` contracts one final time without merging B feature work.
- [ ] Runs the P7 A-owned gate from a clean worktree.
- [ ] Confirms all phase PRs and commit SHAs appear in the final report.
- [ ] Opens the final MR from `feature/implementer-a` to `main`.
- [ ] Stops and returns the MR, evidence, known limits, and integration-pending list to the
  user for the final gate.

