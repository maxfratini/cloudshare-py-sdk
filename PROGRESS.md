# PROGRESS

> Work-item log: what's been done, what's mid-flight, what's next. Hands off state between
> sessions and agents. Not a substitute for the tracker.
>
> **Append-only in substance.** Add new rows at the end. Never delete a row, reorder rows, or
> reword an existing `Description`. Advancing an item means editing its `Status`, `Notes` and
> `Closed` cells in place — that is the intended workflow, not a rewrite of history. An item
> that spans several sessions stays ONE row that changes status, rather than being restated
> each session.
>
> **This file holds live work only.** At the start of a work session, sweep every row already in
> a terminal status (`done`, `dropped`) into `PROGRESS_ARCHIVE.md`, verbatim and keeping its ID.
> `watch` rows are never swept — their rule is still load-bearing.
> Items closed during the current session stay here until the next sweep, so a handoff still
> shows what just landed. That move is the only permitted removal from this file.

| ID      | Status      | Description                      | Notes                                   | Opened     | Closed     | Session        |
|---------|-------------|----------------------------------|-----------------------------------------|------------|------------|----------------|
| PRG-007 | done        | Fix mxCyclopts `command_with_commonopts` for cyclopts v5 | `common_opts` now `Opts \| None = None` (v5 rejects `Parameter(name="*")` without default). 9 skipped tests re-enabled + CLI-parse test added. Module still unused by `cli.py`. | 2026-10-10 | 2026-10-10 | main/Sonnet 5.5 |
| PRG-008 | done        | Run integration tests live; fix `cs_env_create` (404 on `/envs/actions/create`) | Now `POST /envs` w/ `environment`+`itemsCart`; new required kw `project_id`/`region_id`; CLI `env-create` takes both. Mutating integration tests now opt-in via `CLOUDSHARE_TEST_*` ids (never `envs[0]`); added create→delete test. Live run: 9 pass, delete test passed earlier, snapshot_take skips on 403 (account perms). Test envs removed. `class-create` / other legacy paths not re-verified live. | 2026-10-10 | 2026-10-10 | main/Sonnet 5.5 |

**Columns**

- `Status` — `open` · `in-progress` · `blocked` · `watch (YYYY-MM-DD)` · `done` · `dropped`. Nothing else.
- `watch (YYYY-MM-DD)` — fixed, but a rule must keep running for the fix to hold. Not terminal, never swept to the archive. Mostly used in `OPEN_ISSUES.md`; valid here for the same situation.
- `Opened` / `Closed` — `YYYY-MM-DD`, absolute dates only. `Closed` is set only for `done` or `dropped`; `—` otherwise.
- `ID` — never reused, even after the row closes.
- `Session` — who or which agent last moved it, so a handoff has an addressee.
- Keep `Description` to one line. Longer reasoning goes in `Notes`, or behind a link to `plans/<YYYY-MM-DD>-<slug>.md` or an `ARCHITECTURE.md` decision bullet.

## Session notes

Context that is **not** a work item and has nowhere else to live — a flaky CI run, an
environment quirk, a surprise worth warning the next session about. Append dated bullets;
anything that turns out to be actionable becomes a row in the table above instead.

- YYYY-MM-DD — <note>
