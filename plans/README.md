# Plans

> Promoted plans live here — one file per plan, not a single growing doc.
> Update rules: the plan FILES are write-once. If a landed plan changes, add a new dated plan
> for the follow-up rather than editing the old one; a promoted plan is the record of what was
> actually decided, not a living doc. The index table below is the exception: it tracks each
> plan's state and is updated in place.

## Index

| ID       | Status      | Description                     | Notes                                | Opened     | Closed     | File                              |
|----------|-------------|---------------------------------|--------------------------------------|------------|------------|-----------------------------------|
| PLAN-001 | done        | <what the plan sets out to do>  | <outcome; link the PR if there is one>| YYYY-MM-DD | YYYY-MM-DD | `YYYY-MM-DD-<slug>.md`            |
| PLAN-002 | in-progress | <...>                           | <which steps are left>               | YYYY-MM-DD | —          | `YYYY-MM-DD-<slug>.md`            |
| PLAN-003 | dropped     | <...>                           | <superseded by PLAN-00n, and why>    | YYYY-MM-DD | YYYY-MM-DD | `YYYY-MM-DD-<slug>.md`            |

**Columns**

- `Status` — `open` (promoted, not started) · `in-progress` · `blocked` · `done` (landed) · `dropped` (abandoned or superseded). Nothing else.
- `Opened` — the plan's own date, the one in its filename. `Closed` — the date the work landed or was abandoned; `—` while the plan is live.
- `ID` — never reused. `File` — the plan's filename in this directory.
- A `dropped` plan's file stays here. Superseding a plan does not delete it; the record of what was decided and then abandoned is the point.

## What goes here

A plan worth keeping with the code: something you'd want to link from a PR,
hand to a reviewer, or find again in six months to see why a change was shaped
the way it was. Not every `ExitPlanMode` plan earns this — most are throwaway.

## How a plan gets here

Not auto-synced. Promotion is explicit: copy the approved plan from Claude
Code's own plan storage (`~/.claude/plans/` by default, or the project's
configured `plansDirectory`) into this directory, e.g. via `/plan-save`, which
also adds the index row above.

## Naming

`plans/<YYYY-MM-DD>-<slug>.md` — keep the original date; it's part of the record.
