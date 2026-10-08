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
| PRG-001 | done        | Project review & plan created    | Comprehensive audit of cloudshare project; plan at plans/2026-10-07-cloudshare-review.md | 2026-10-07 | 2026-10-07 | nimbalyst-coach |
| PRG-002 | done        | Fix wrapper_cls.py bug (P1-1)    | Fixed by PRG-003's partial refactor: `.cs_get()` → `.get()`, `dct` → `new_dct` | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-003 | done        | Replace pandas with dict-flattener (P1-2) | Finished by fix-4: 8 ruff errors fixed, config wiring, make check green. pandas removed from deps/source. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-004 | done        | Add tests for mxcloudshare.py SDK (P1-3) | tests/test_mxcloudshare_sdk.py: 22 pre-existing-helpers + P2-1 auth refactor. tests/test_mxlogging.py (20), test_mxcyclopts.py (21), test_wrapper.py (19). All landed. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-005 | done        | API gap-closure plan executed   | PLAN-002 lanes L1–L7 + Phase 3 all done. Final: 74 cs_ helpers, ~63 CLI commands, 189 tests, make check green. From 16% → 100% endpoint reachable via CLI. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-006 | done        | PLAN-001 execution (P2/P3/P4)   | 12/15 PLAN-001 items landed. P2-1/P3-2/P3-3/P3-4/P2-2/P2-3/P2-4/P3-1/P3-5/P3-6/P4-2/P4-3 done. P3-2/3/4 included --version, --dry-run, --json. P4-1 blocked (sandbox creds). mxCyclopts 9 test skips pre-existing (cyclopts v5 bug out of scope). | 2026-10-07 | 2026-10-07 | main/big-pickle |

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
