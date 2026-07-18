# Implementer A P0 Seed and Gate Task Appendix

> Read `a-p0-foundation.md` first. This appendix is part of the same approved P0 phase brief package and continues its numbering, constraints, interfaces, and TDD workflow.

### Task 4: Persist the org seed transactionally and idempotently

**Files:**
- Create: `backend/evermind/org/seed_service.py`
- Create: `backend/tests/p0/test_seed_service.py`

**Interfaces:**
- Consumes: `OrgSeed`, fixed ID maps, an existing SQLAlchemy `Session`.
- Produces: `seed_org(session: Session, seed: OrgSeed) -> SeedSummary`.
- Transaction ownership: `seed_org` validates, merges, and flushes but never commits; its
  caller owns commit/rollback.

- [ ] **Step 1: Write database-backed seed tests**

Create `backend/tests/p0/test_seed_service.py`:

```python
from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import ProjectKind, ProjectStatus
from evermind.org.models import Project, User, UserIdentity, UserTeam
from evermind.org.seed_ids import PROJECT_IDS, TEAM_IDS, USER_IDS
from evermind.org.seed_schema import load_org_seed
from evermind.org.seed_service import seed_org

ORG_FIXTURE = Path(__file__).resolve().parents[3] / "data-v2" / "org.json"


def test_seed_is_idempotent_and_keeps_stable_relationships(db_session: Session):
    seed = load_org_seed(ORG_FIXTURE)
    first = seed_org(db_session, seed)
    second = seed_org(db_session, seed)
    db_session.flush()

    assert first == second
    assert first.projects == 2
    assert first.teams == 2
    assert first.groups == 2
    assert first.users == 9
    assert first.identities == 9
    assert first.memberships == 11
    assert first.parties == 5

    linh = db_session.get(User, USER_IDS["linh"])
    mai = db_session.get(User, USER_IDS["mai"])
    thao = db_session.get(User, USER_IDS["thao"])
    assert linh is not None
    assert mai is not None
    assert thao is not None
    assert mai.manager_id == linh.id
    assert thao.manager_id == mai.id

    khoa_teams = set(
        db_session.scalars(
            select(UserTeam.team_id).where(UserTeam.user_id == USER_IDS["khoa"])
        )
    )
    thao_teams = set(
        db_session.scalars(
            select(UserTeam.team_id).where(UserTeam.user_id == USER_IDS["thao"])
        )
    )
    assert khoa_teams == {TEAM_IDS["TEAM-EV"], TEAM_IDS["TEAM-ED"]}
    assert thao_teams == {TEAM_IDS["TEAM-EV"], TEAM_IDS["TEAM-ED"]}

    linh_identity = db_session.get(UserIdentity, USER_IDS["linh"])
    assert linh_identity is not None
    assert linh_identity.platform == "generic-chat"
    assert linh_identity.connector_scope == "data-v2"

    trung_thu = db_session.get(Project, PROJECT_IDS["P-TT"])
    assert trung_thu is not None
    assert trung_thu.end_date == date(2026, 9, 26)
    assert db_session.scalar(select(User).where(User.handle == "trang")) is None


def test_seed_never_deletes_an_unrelated_project(db_session: Session):
    unrelated = Project(
        id=999,
        name="Unrelated project",
        kind=ProjectKind.PROGRAM,
        end_date=None,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(unrelated)
    db_session.flush()

    seed_org(db_session, load_org_seed(ORG_FIXTURE))

    assert db_session.get(Project, 999) is not None


def test_seed_advances_surrogate_id_sequences(db_session: Session):
    seed_org(db_session, load_org_seed(ORG_FIXTURE))
    project = Project(
        name="Created after seed",
        kind=ProjectKind.PROGRAM,
        end_date=None,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.flush()
    assert project.id > max(PROJECT_IDS.values())
```

- [ ] **Step 2: Run the seed service tests and verify RED**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run pytest -q tests/p0/test_seed_service.py
```

Expected: collection fails because `seed_service` does not exist.

- [ ] **Step 3: Implement the seed summary and persistence order**

Create `backend/evermind/org/seed_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from evermind.org.models import ChatGroup, Party, Project, Team, User, UserIdentity, UserTeam
from evermind.org.seed_ids import (
    GROUP_IDS,
    PARTY_IDS,
    PROJECT_IDS,
    TEAM_IDS,
    USER_IDS,
    validate_seed_keys,
)
from evermind.org.seed_schema import OrgSeed

_SEQUENCE_TABLES = (
    "projects",
    "teams",
    "chat_groups",
    "users",
    "user_identities",
    "parties",
)


@dataclass(frozen=True)
class SeedSummary:
    projects: int
    teams: int
    groups: int
    users: int
    identities: int
    memberships: int
    parties: int


def _advance_sequences(session: Session) -> None:
    for table_name in _SEQUENCE_TABLES:
        session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                f"(SELECT MAX(id) FROM {table_name}), true)"
            )
        )


def seed_org(session: Session, seed: OrgSeed) -> SeedSummary:
    validate_seed_keys(seed)

    for row in seed.projects:
        session.merge(
            Project(
                id=PROJECT_IDS[row.id],
                name=row.name,
                kind=row.kind,
                end_date=row.end_date,
                status=row.status,
            )
        )

    for row in seed.teams:
        session.merge(
            Team(id=TEAM_IDS[row.id], project_id=PROJECT_IDS[row.project_id], name=row.name)
        )

    for row in seed.chat_groups:
        session.merge(
            ChatGroup(
                id=GROUP_IDS[row.id],
                platform=row.platform,
                platform_chat_id=row.platform_chat_id,
                project_id=PROJECT_IDS[row.project_id],
                team_id=TEAM_IDS[row.team_id] if row.team_id is not None else None,
            )
        )

    for row in seed.users:
        session.merge(
            User(
                id=USER_IDS[row.handle],
                name=row.name,
                handle=row.handle,
                role_rank=row.role_rank,
                manager_id=None,
                status=row.status,
                departed_at=None,
            )
        )
    session.flush()

    for row in seed.users:
        session.merge(
            User(
                id=USER_IDS[row.handle],
                name=row.name,
                handle=row.handle,
                role_rank=row.role_rank,
                manager_id=USER_IDS[row.manager] if row.manager is not None else None,
                status=row.status,
                departed_at=None,
            )
        )
        session.merge(
            UserIdentity(
                id=USER_IDS[row.handle],
                user_id=USER_IDS[row.handle],
                platform="generic-chat",
                connector_scope="data-v2",
                platform_user_id=row.platform_user_id,
            )
        )

    for row in seed.user_teams:
        session.merge(
            UserTeam(
                user_id=USER_IDS[row.user],
                team_id=TEAM_IDS[row.team],
                role_in_team=row.role_in_team,
            )
        )

    for row in seed.parties:
        session.merge(
            Party(
                id=PARTY_IDS[row.id],
                name=row.name,
                aliases=list(row.aliases),
                kind=row.kind,
                contact_note=row.contact_note,
            )
        )

    session.flush()
    _advance_sequences(session)
    return SeedSummary(
        projects=len(seed.projects),
        teams=len(seed.teams),
        groups=len(seed.chat_groups),
        users=len(seed.users),
        identities=len(seed.users),
        memberships=len(seed.user_teams),
        parties=len(seed.parties),
    )
```

The fixed `_SEQUENCE_TABLES` tuple is internal code, never fixture input. Do not catch and
suppress database or validation exceptions; the caller's transaction rolls back atomically.

- [ ] **Step 4: Run focused tests and verify GREEN**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run pytest -q tests/p0/test_seed_service.py
```

Expected: idempotency, relationships, stable identities, and unrelated-row preservation pass.

- [ ] **Step 5: Run all P0 tests**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run pytest -q tests/p0
```

Expected: migration, seed-contract, and seed-service tests all pass.

- [ ] **Step 6: Commit transactional seed persistence**

```bash
cd "$(git rev-parse --show-toplevel)"
git add backend/evermind/org/seed_service.py backend/tests/p0/test_seed_service.py
git commit -m "feat(org): persist the v2 seed idempotently"
```

---

### Task 5: Add the seed CLI used by `make seed`

**Files:**
- Create: `backend/evermind/org/seed.py`
- Create: `backend/tests/p0/test_seed_cli.py`

**Interfaces:**
- Consumes: `load_org_seed`, `seed_org`, and `SessionLocal`.
- Produces: `python -m evermind.org.seed PATH`, exit code zero, and a JSON count summary.

- [ ] **Step 1: Write a focused CLI parsing test**

Create `backend/tests/p0/test_seed_cli.py`:

```python
from pathlib import Path

from sqlalchemy.orm import Session

from evermind.org.seed import run_seed

ORG_FIXTURE = Path(__file__).resolve().parents[3] / "data-v2" / "org.json"


def test_run_seed_loads_fixture_and_returns_summary(db_session: Session):
    summary = run_seed(ORG_FIXTURE, db_session)
    assert summary.users == 9
    assert summary.memberships == 11
```

- [ ] **Step 2: Run the test and verify RED**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run pytest -q tests/p0/test_seed_cli.py
```

Expected: collection fails because `evermind.org.seed` does not exist.

- [ ] **Step 3: Implement the thin CLI**

Create `backend/evermind/org/seed.py`:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path

from sqlalchemy.orm import Session

from evermind.db.session import SessionLocal
from evermind.org.seed_schema import load_org_seed
from evermind.org.seed_service import SeedSummary, seed_org


def run_seed(path: Path, session: Session) -> SeedSummary:
    return seed_org(session, load_org_seed(path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed EverMind org data")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    with SessionLocal.begin() as session:
        summary = run_seed(args.path, session)
    print(json.dumps(asdict(summary), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused and real CLI checks**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run pytest -q tests/p0/test_seed_cli.py
uv run python -m evermind.org.seed ../data-v2/org.json
uv run python -m evermind.org.seed ../data-v2/org.json
```

Expected: the test passes; both CLI runs print the same seven counts and return zero.

- [ ] **Step 5: Commit the CLI**

```bash
cd "$(git rev-parse --show-toplevel)"
git add backend/evermind/org/seed.py backend/tests/p0/test_seed_cli.py
git commit -m "feat(org): add the v2 seed command"
```

---

### Task 6: Correct stale executable-fixture documentation

**Files:**
- Modify: `data-v2/README.md`
- Modify: `ai-docs/testing-strategy.md`

**Interfaces:**
- Consumes: the unchanged files `data-v2/meeting-2026-09-07.txt` and
  `data-v2/answer_key.json`.
- Produces: prose counts that agree with the executable fixtures.

- [ ] **Step 1: Verify the counts mechanically**

```bash
python3 - <<'PY'
import json
from pathlib import Path

turns = [line for line in Path('data-v2/meeting-2026-09-07.txt').read_text().splitlines()
         if line.strip().startswith('[')]
answer = json.loads(Path('data-v2/answer_key.json').read_text())
print({'transcript_turns': len(turns), 'chat_decisions': len(answer['decisions'])})
PY
```

Run from the repository root. Expected:

```text
{'transcript_turns': 38, 'chat_decisions': 18}
```

- [ ] **Step 2: Update only stale prose**

In `data-v2/README.md`:

- Change `15 chat decisions` to `18 chat decisions`.
- Change `30 turns` to `38 turns`.
- State that batch 25 yields transcript windows of 25 and 13 turns, while batch 100 yields
  one 38-turn flush-on-upload window.

In `ai-docs/testing-strategy.md`:

- Pin 38 transcript turns and both window profiles in L0.
- Change the L4 expectation from 15 to 18 chat decisions.

Do not change the B-owned L0 test file; record its stale explanatory comment as an external
documentation follow-up because its asserted behavior already pins 38 correctly.

- [ ] **Step 3: Run L0 and verify no fixture changed**

```bash
(cd backend && uv run pytest -q tests/test_fixtures_l0.py)
git diff --exit-code -- data-v2/corpus.jsonl data-v2/answer_key.json \
  data-v2/meeting-2026-09-07.txt data-v2/org.json
```

Expected: seven tests pass; none of the executable fixtures changed.

- [ ] **Step 4: Commit the documentation correction**

```bash
git add data-v2/README.md ai-docs/testing-strategy.md
git commit -m "docs: align fixture counts with data v2"
```

---

### Task 7: Run the P0 gate and record the phase

**Files:**
- Create or modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: all P0 commits and the disposable PostgreSQL container.
- Produces: a frozen candidate SHA, exact gate evidence, and changelog entries for the P0
  implementation commits.

- [ ] **Step 1: Run the complete P0 backend gate**

From the repository root:

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run alembic current
uv run pytest -q
uv run ruff check .
uv run lint-imports
uv run mypy evermind/config.py evermind/db evermind/org evermind/decisions/models.py
```

Expected: Alembic reports `0002`; all tests, lint, import rules, and A-scoped type checks pass.
A pre-existing failure in an A-owned file must be fixed rather than hidden with a broad ignore.

- [ ] **Step 2: Verify migration replay one final time**

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind'
uv run alembic downgrade 0001
uv run alembic upgrade head
uv run python -m evermind.org.seed ../data-v2/org.json
uv run python -m evermind.org.seed ../data-v2/org.json
uv run pytest -q tests/p0
```

Expected: both migration directions succeed; seed output is identical; P0 tests pass.

- [ ] **Step 3: Verify the public P0 commands and API skeleton**

Run from the repository root:

```bash
DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind' make seed
cd backend
DATABASE_URL='postgresql+psycopg://evermind:evermind@localhost:55432/evermind' \
  uv run python - <<'PY'
from fastapi.testclient import TestClient

from evermind.api.main import app

response = TestClient(app).get('/healthz')
assert response.status_code == 200
assert response.json() == {'status': 'ok'}
PY
```

Expected: `make seed` prints the stable summary and `/healthz` returns the exact skeleton
response. Full Compose/demo startup remains B-owned integration work.

- [ ] **Step 4: Stop only the approved disposable container**

```bash
docker stop evermind-a-p0-db
```

Expected: Docker stops and automatically removes the `--rm` container. No volume or existing
developer database is touched.

- [ ] **Step 5: Record implementation commit SHAs and timestamps**

```bash
cd "$(git rev-parse --show-toplevel)"
git log --reverse --format='%H %cI %s' feature/implementer-a..HEAD
```

Create or update `CHANGELOG.md` with a P0 section containing the exact output SHAs and ISO
timestamps plus a concise description of each change. Use the returned values directly; do
not write symbolic or placeholder SHAs.

- [ ] **Step 6: Commit the changelog**

```bash
cd "$(git rev-parse --show-toplevel)"
git add CHANGELOG.md
git commit -m "docs: record Implementer A P0 changes"
```

- [ ] **Step 7: Freeze and report the candidate**

```bash
cd "$(git rev-parse --show-toplevel)"
git status --short
git log -1 --format='%H %cI %s'
git diff --check feature/implementer-a...HEAD
```

Expected: clean worktree, one candidate SHA, and no whitespace errors. Return the SHA and all
gate command results to the coordinator. Do not merge; independent reviewer and tester
specialists run next.

