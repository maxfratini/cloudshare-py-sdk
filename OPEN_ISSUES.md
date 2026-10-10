# OPEN ISSUES

> Snapshot of blockers, bugs and deferred work, so an agent sees them without a tracker call.
> If this project has a tracker (Linear / GitHub Issues / Jira), name it here — **the tracker is
> the source of truth**, use its IDs in the `ID` column, and it wins on any disagreement. If there
> is no tracker, say so here instead: this file is then the source of truth.
> Do not invent issues here.

| ID      | Status      | Description                     | Notes                              | Opened     | Closed     | Kind     | Owner | Link    |
|---------|-------------|---------------------------------|------------------------------------|------------|------------|----------|-------|---------|
| ISS-001 | open        | <one-line symptom or blocker>   | <impact, workaround, how to repro> | YYYY-MM-DD | —          | blocker  | <who> | <url>   |
| ISS-002 | in-progress | <one-line symptom>              | <what's been ruled out so far>     | YYYY-MM-DD | —          | bug      | <who> | <url>   |
| ISS-003 | watch (YYYY-MM-DD) | <defect that is fixed>   | <the rule that must keep running> | YYYY-MM-DD | —          | watch    | <who> | <url>   |
| ISS-004 | dropped     | <thing we chose not to do>      | <why not, and what would reopen it>| YYYY-MM-DD | YYYY-MM-DD | deferred | <who> | —       |
| ISS-005 | watch (2026-10-07) | Legacy undocumented API paths kept in production use | Rule: keep `cs_blueprint_get_all` (`/blueprints`), `cs_policy_get_all` (`/policies`) working unchanged (PLAN-002 D3); project-scoped official helpers exist alongside. Both are covered by live tests in `tests/test_integration.py`. `POST /envs/actions/create` was dropped from this rule: it 404s live, `cs_env_create` now uses `POST /envs` (2026-10-09). Reopen if CloudShare drops the legacy paths. | 2026-10-07 | —          | watch    | —     | plans/2026-10-07-api-gap-closure.md |
| ISS-006 | done        | No sandbox integration suite (PLAN-001 P4-1) | Landed and verified live 2026-10-09 (`make integration`: 10 passed, 3 skipped without opt-in vars). Lifecycle test (create, ready, suspend, resume, delete) passed against the account with `CLOUDSHARE_TEST_{BLUEPRINT,REGION,POLICY}_ID`. suspend/resume on a pinned env passed 2026-10-08; snapshot-take gets 403 on this account, so it skips. Old delete-first-env test removed (unsafe). | 2026-10-07 | 2026-10-09 | deferred | —     | plans/2026-10-07-cloudshare-review.md |
| ISS-007 | done        | `mxCycloptsApp.command_with_commonopts` incompatible with cyclopts >= 5 | `_apply_commonopts` adds `common_opts` without a default; cyclopts 5 raises ValueError at registration. 9 tests in `tests/test_mxcyclopts.py` skipped. Decorator is unused by `cli.py`, so CLI is unaffected. Fixed 2026-10-10 (PRG-007): `common_opts` is now `Opts | None = None`; the 9 tests are re-enabled. | 2026-10-07 | 2026-10-10 | bug      | —     | —       |

**Columns**

- `Status` — `open` · `in-progress` · `blocked` · `watch (YYYY-MM-DD)` · `done` · `dropped`. Nothing else.
- `Kind` — `blocker` (stops other work) · `bug` (wrong behaviour, not blocking) · `watch` (fixed, but a rule must keep running) · `deferred` (consciously not doing it for now; the reason goes in `Notes`).
- `blocker` is reserved for rows that are still OPEN. Once something stops blocking, it moves to another `Kind` — a blocker row is never left sitting in a closed state.
- `watch` — a defect that is **fixed, but whose rule stays active**: a guard, lint, prune step or convention that must keep running for the fix to hold. Put the rule in `Notes`, so a future reader knows what must not be deleted. The fix date goes **inside the `Status` cell** (`watch (2026-10-01)`), not in `Closed`.
- `Opened` / `Closed` — `YYYY-MM-DD`. `Closed` is set only for `done` or `dropped`; `—` otherwise, including for `watch` (its date lives in `Status`, which keeps `Closed` meaning "this row is finished and archivable").
- `ID` — never reused, even after the row closes. Use the tracker's ID if there is a tracker.

**Updating** — append new rows at the end. Never delete a row, reorder rows, or reword an existing
`Description`; close an item by editing its `Status`, `Notes` and `Closed` cells in place.

**This file holds live issues only.** At the start of a work session, sweep every row already in a
terminal status (`done`, `dropped`) into `OPEN_ISSUES_ARCHIVE.md`, verbatim and keeping its ID.
**`watch` rows are never swept** — they stay here on purpose, because their rule is still
load-bearing and someone has to notice if it gets removed. A watch row leaves only by being
re-opened (the fix regressed) or by moving to `done` once its rule is retired.
Items closed during the current session stay here until the next sweep. That move is the only
permitted removal from this file, and IDs are never reused after archiving.
