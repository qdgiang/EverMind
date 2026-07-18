# Implementer A Charter

## Purpose

This charter is the stable operating contract for the complete Implementer A campaign.
Implementer A owns EverMind's write spine from P0 through P7, while each phase is executed
in a fresh context on its own branch and passes independent implementation, review, and test
gates before it is merged into `feature/implementer-a`.

The charter is versioned product-development guidance. Local Codex agent files are thin
runtime adapters and must point here rather than copy business rules into their prompts.

## Source precedence

Use the current branch, never remembered context. When sources disagree, apply this order:

1. Shared contracts already merged into `main`, synchronized into the current A branch.
2. `ai-docs/work-split.md` for module ownership and A↔B interfaces.
3. Per-debate resolutions, `ai-docs/design-v2.md`, and `ai-docs/data-model.md` for business
   and persistence semantics.
4. `ai-docs/features.md`, `ai-docs/architecture.md`, `ai-docs/testing-strategy.md`, and
   `ai-docs/plan.md` in that order for build guidance and gates.
5. `ai-docs/scenarios/` and `data-v2/` as executable examples and fixture contracts.
6. The active phase brief for bounded implementation steps.

Additional interpretation rules:

- `frontend_ref/` is EverMind's authoritative final UI design. Its mock data is not domain
  truth, but its visual language, layout, component patterns, and responsive behavior are.
- `.claude/agents/*.md` and the stakeholder XLSX files are templates or historical reference
  only. They do not define the current stack, schema, permissions, or behavior.
- Open GitHub issues are not implementation blockers and must not be solved speculatively.
  Implement the merged contracts and canonical docs.
- For executable fixture counts, the files in `data-v2/` and `answer_key.json` win over stale
  prose counts. The current fixture has 38 transcript turns and 18 chat decisions.

## Ownership

Implementer A may change the following vertically, including their owned API and UI:

- `backend/evermind/org/`
- `backend/evermind/llm/`
- `backend/evermind/ingestion/`
- `backend/evermind/decisions/`
- `backend/evermind/knowledge/`
- A-owned portions of `backend/evermind/api/`
- Shared database foundation and corrective migrations assigned to A
- `frontend/app/decisions/`, `frontend/app/qa/`, A-owned proposal surfaces, and the shared
  typed command client
- A-owned tests, evaluation harnesses, and implementation documentation

Implementer A must not change these B-owned areas:

- `backend/evermind/connectors/`
- `backend/evermind/tasks/`
- `backend/evermind/signals/`
- `backend/evermind/surfacing/`
- `backend/evermind/scheduler/`
- Frontend shell and B-owned dashboard views
- Shared infrastructure or CI workflows

The only approved infrastructure action is setting the GitHub Actions secret `AI_API_KEY`.
Live-eval CI wiring remains an external B dependency; A runs live evaluation locally as a
blocking gate.

## Campaign and branches

The campaign uses this topology:

```text
main
└── feature/implementer-a
    ├── feat/a-p0-foundation
    ├── feat/a-p1-decisions
    ├── feat/a-p2-ingestion
    ├── feat/a-p3-acts
    ├── feat/a-p4-api-dashboard
    ├── feat/a-p5-knowledge
    ├── feat/a-p6-retrieval
    └── feat/a-p7-hardening
```

This is an explicit A-campaign override to `work-split.md`'s default instruction that phase
PRs target `main`. A phase PR targets `feature/implementer-a`. Shared contract changes still
land separately on `main` and are synchronized into A before dependent work begins.

For each phase:

1. Synchronize the current `main` contracts into `feature/implementer-a`.
2. Create the phase branch and an isolated worktree from the updated integration branch.
3. Give the implementer the charter, master plan, and exactly one current phase brief package;
   a package may split long task appendices into directly linked files to keep commits small.
4. Freeze the candidate SHA when implementation checks pass.
5. Run independent reviewer and tester specialists against that SHA.
6. Return failures to the implementer and repeat both gates after fixes.
7. When both gates pass, the coordinator merges with a merge commit into
   `feature/implementer-a` without waiting for a manual phase approval.
8. Create the next phase brief from the newly merged state.

After P7, the coordinator prepares a final MR from `feature/implementer-a` to `main` and a
complete evidence report. The user remains the final human gate and the agent must not merge
that MR.

## Specialist roles

### Implementer

- Reads the active plan completely before editing.
- Uses test-first RED/GREEN/refactor cycles for each behavior.
- Changes only A-owned files named by the phase brief.
- Keeps functions and files focused, avoids speculative dependencies and abstractions, and
  preserves validation, authorization, security, accessibility, and data-loss protections.
- Does not merge its own candidate.

### Reviewer

- Reviews the frozen diff read-only against contracts, ownership, canonical semantics,
  security, performance, and minimal-safe implementation rules.
- Checks what can be deleted, reused, replaced with native behavior, or deferred after
  correctness and safety are established.
- Returns `PASS` only when no blocking finding remains.

### Tester

- Starts from the same frozen SHA and runs the exact phase commands independently.
- Verifies expected failures were observed before implementation and focused plus broader
  checks pass afterward.
- Never edits production code to make a test pass.
- Returns command output, environment notes, and a `PASS` or `FAIL` verdict.

### Coordinator

- Owns worktrees, branch hygiene, phase briefs, PR evidence, and merge commits.
- Never treats a specialist claim as evidence without a command result or concrete review
  finding.
- Does not weaken a gate, change a shared contract inside a feature PR, or cross into B-owned
  modules to unblock A.

## A↔B dependency policy

Use only the nine published interfaces in `work-split.md`. If B's implementation is not
available, inject a contract fake or protocol-compatible test double on the A side. Do not
read or write B's internal tables and do not patch B's services.

An A phase may pass when its owned implementation and contract tests pass. Record missing
real integration as `integration-pending` with the expected request, response, event, or port
shape. A↔B merge and full-system integration are outside this campaign.

If a merged shared contract makes a mandatory A behavior impossible, complete unaffected A
work, preserve evidence, and stop that phase at its gate. Do not silently alter the contract.

## Persistence and fixture rules

- Migration `0001` is already merged and is immutable. Corrective schema work starts at
  `0002`; tests cover both `0001 → head` and a clean database to `head`.
- Do not reset or delete an existing database to make a migration pass.
- `data-v2/org.json` string fixture keys map to explicit deterministic integer IDs. Unknown
  keys fail validation instead of being hashed or guessed.
- The seed loader is transactional and idempotent. Re-running it updates the same seed-owned
  rows and never deletes unrelated rows.
- Decisions are append-only; tasks remain projections; proposals never expire; and A adds no
  outbound chat capability.

## LLM policy

- LLM paths use the real OpenAI-compatible DeepSeek endpoint by default.
- Domain, authorization, migration, and reducer tests remain network-free because they do
  not test an LLM path.
- Load the local key from `/Users/phungminh/Code/VAIC/APIKey-Deepseek.txt` into
  `AI_API_KEY` without printing or copying it into the repository.
- The coordinator may set the repository secret `AI_API_KEY` through GitHub CLI, but A does
  not modify B-owned workflow files.
- P2 and every prompt/model-changing phase run blocking live evaluation. Recorded responses
  also remain available for deterministic regression.
- Never log credentials. Call records may include model, token counts, latency, attempt count,
  and fixture-safe request identifiers.

## Frontend policy

- A implements only DSH-4 decision/policy logs, DSH-6 Q&A, and DSH-7 proposal/command
  surfaces.
- Preserve `frontend_ref/` composition, color system, spacing, information density,
  interactions, and responsive behavior. Replace mock content with real contracts; do not
  redesign the product.
- Consume B's shell and shared navigation as they exist. Raise shell mismatches as
  integration notes rather than editing B-owned components.
- Before frontend work, the implementer reads the available `frontend-design`,
  `design-taste-frontend`, Next.js/React, and accessibility/review skills named by the phase
  brief.

## Quality and merge gates

- A feature ships with focused tests in the same PR.
- Every implementation behavior shows an expected RED test before production code and a
  GREEN focused test plus broader regression afterward, except approved generated or
  configuration-only changes.
- Keep each commit under 700 changed lines. Use multiple coherent commits inside a phase PR.
- The phase changelog commit records implementation commit SHAs and precise timestamps.
- Never weaken thresholds to merge. L2 requires decision precision at least 0.90, linkage
  accuracy at least 0.80, planted-boundary citation completeness of 100%, four correct marker
  records, and both batch-size profiles 25 and 100.
- P6 measures structured/keyword retrieval first. If no measured recall miss exists, an
  evidence report that declines pgvector is the correct minimal completion.
- File deletion requires explicit user approval for the exact target.

## Fresh-context bootstrap checklist

Before implementation, every A specialist confirms:

- The active branch and worktree are correct and clean.
- `main` contracts have been synchronized as instructed by the coordinator.
- Global `/Users/phungminh/.claude/CLAUDE.md`, this charter, the master plan, and every file in
  the active phase brief package have been read completely.
- The files listed in the phase brief still exist and their current contents match the plan's
  assumptions.
- No B-owned file is in the proposed write set.
- The implementation plan has received the campaign-level explicit approval recorded by the
  coordinator.
