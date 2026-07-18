# EverMind E2E Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make replayed or uploaded source material produce visible, attributable EverMind decisions and tasks, and let a selected dashboard persona inspect and act on that state.

**Architecture:** Keep the existing one-write pipeline intact. A small ingestion orchestrator parses deterministic markers first, submits only typed commands through `DecisionsService`, then advances task/feed projections. The dashboard uses one shared handle-based persona source for every REST request and renders errors rather than replacing them with empty states. LLM extraction remains behind the existing gateway and is invoked only for non-marker windows.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Next.js App Router, React, Tailwind, Playwright CLI.

## Global Constraints

- Decisions remain append-only; task rows are projections only.
- Every chat-originated command has an evidence citation pinned to its message revision.
- Persona is demo-only but is always a backend user handle, never a numeric id.
- The bot remains read-only; no connector may send chat messages.
- Do not add dependencies unless the existing stack cannot supply the requirement.

---

### Task 1: Freeze and test the dashboard/API contract

**Files:**
- Modify: `backend/evermind/api/routers/decisions_router.py`, `backend/evermind/api/routers/connectors_router.py`
- Modify: `frontend/lib/types.ts`, `frontend/lib/api-client.ts`, `frontend/components/shell/Topbar.tsx`
- Create: `backend/tests/scenarios/test_api_contracts.py`

**Interfaces:**
- `GET /personas` returns `{id, handle, name, role_rank, status}`.
- All authenticated frontend requests send `X-Persona: <handle>`.
- `GET /decisions` returns filtered decision summaries and never raises `NotImplementedError`.

- [ ] Add API tests that prove numeric persona headers are rejected and seeded handles are accepted.
- [ ] Add an API test for decisions filtering by status/search and `show_inactive`.
- [ ] Implement the router with SQL queries over `Decision`, returning stable JSON summaries.
- [ ] Replace frontend numeric/hard-coded personas with API-loaded handles, persisted client-side and provided to reads/writes/uploads.
- [ ] Replace silent fetch catches with a reusable error state that shows HTTP failures.
- [ ] Run targeted pytest and `npm run build`.

### Task 2: Materialize deterministic marker decisions through the only write path

**Files:**
- Modify: `backend/evermind/ingestion/service.py`, `backend/evermind/connectors/replay.py`, `backend/evermind/api/routers/connectors_router.py`
- Modify: `backend/evermind/tasks/consumer.py`, `backend/evermind/surfacing/service.py` as required to project emitted events
- Create: `backend/tests/scenarios/test_marker_e2e.py`

**Interfaces:**
- `IngestionService.apply_markers(message_id) -> list[dict]` parses supported marker messages.
- Each materialization is unique on the existing marker identity and calls `DecisionsService.handle` with `ProposeDecision` or `RecordTaskUpdate`.
- `run_replay` invokes marker materialization after each persisted source message.

- [ ] Write tests for `!decision` and `!blocked` producing one cited command, one task projection, and no duplicate on replay retry.
- [ ] Implement a narrow marker grammar: `!decision <description>` and `!blocked <description>`, with a `T-<id>` target when present and `NEW_TASK` otherwise.
- [ ] Resolve the message author through the seeded handle, stamp `created_from=marker`, cite the current message revision, and route through `DecisionsService`.
- [ ] Poll the existing task projection consumer after a successful command and generate a minimal persona feed/inbox entry from resulting events.
- [ ] Invoke marker ingestion from replay and transcript upload; leave non-marker messages stored for the later LLM window lane.
- [ ] Run the focused tests and a compose seed/replay smoke.

### Task 3: Complete the dashboard read/write vertical slice

**Files:**
- Modify: `frontend/app/feed/page.tsx`, `frontend/app/tasks/page.tsx`, `frontend/app/decisions/page.tsx`, `frontend/app/upload/page.tsx`
- Create: `frontend/components/dashboard/PersonaProvider.tsx`, `frontend/components/dashboard/ApiError.tsx`, `frontend/components/dashboard/DecisionForm.tsx`
- Modify: `backend/evermind/api/main.py`
- Create: `backend/tests/scenarios/test_dashboard_command_e2e.py`

**Interfaces:**
- The dashboard command form submits a complete `propose_decision` envelope using a handle-backed persona.
- API command handling advances task projections before returning.
- Feed/inbox/task/decision views share the same selected persona and show failures explicitly.

- [ ] Add API tests for a dashboard `propose_decision` command that creates a visible task and subsequent decision list row.
- [ ] Make command processing synchronously advance the task projection, preserving the domain gateway as the sole writer.
- [ ] Add a compact proposal form for a new task and render status/error/receipt outcome.
- [ ] Implement decision-log filtering and useful empty/error states.
- [ ] Validate with frontend build and Playwright against Compose.

### Task 4: Restore knowledge and transcript outcomes

**Files:**
- Modify: `backend/evermind/knowledge/service.py`, `backend/evermind/api/routers/knowledge_router.py`
- Modify: `frontend/app/qa/page.tsx`
- Create: `backend/tests/scenarios/test_knowledge_api.py`

**Interfaces:**
- `KnowledgeService.answer(question, persona)` returns `{answer, citations}` without using uncited raw text as a decision claim.
- `POST /qa` returns a 200 response for a supported task/decision lookup and a safe no-answer response otherwise.

- [ ] Add tests for decision/task keyword retrieval and citation presence.
- [ ] Implement structured SQL retrieval over effective decisions and projected tasks; clearly label pending decisions and return a no-answer result when there is no grounded evidence.
- [ ] Add the interactive Q&A form and receipt rendering.
- [ ] Verify the transcript upload creates an ingestion outcome or reports that the source was stored awaiting non-marker extraction.

### Task 5: Add the L4 regression net and handoff

**Files:**
- Create: `backend/tests/test_e2e_smoke.py`
- Modify: `Makefile`, `.github/workflows/ci.yml`, `ai-docs/runbook.md`

**Interfaces:**
- A recorded smoke proves seed → replay → marker materialization → task/feed/decision → dashboard command → Q&A.

- [ ] Write an isolated Postgres/SQLite-safe E2E test with marker fixtures; assert duplicate replay does not duplicate a decision.
- [ ] Add a Make target that runs the recorded smoke without a live LLM key.
- [ ] Add the smoke to CI and record the Compose/UI verification steps in the runbook.
- [ ] Run the backend suite, lint/import contracts, frontend production build, Compose smoke, and Playwright screenshots.
- [ ] Review the diff for contract drift, hard-coded personas, uncaught API errors, and secrets before committing and opening the PR.
