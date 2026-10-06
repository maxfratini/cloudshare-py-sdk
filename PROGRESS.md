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
| PRG-001 | done        | <what shipped, one line>         | <anything a follow-up should know>      | YYYY-MM-DD | YYYY-MM-DD | <who / agent>  |
| PRG-002 | in-progress | <what's mid-flight>              | <where it stands, what's left>          | YYYY-MM-DD | —          | <who / agent>  |
| PRG-003 | blocked     | <what can't proceed>             | <what's blocking it; link `ISS-00n`>    | YYYY-MM-DD | —          | <who / agent>  |
| PRG-004 | open        | <the obvious next step>          | <why it's next>                         | YYYY-MM-DD | —          | —              |

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
