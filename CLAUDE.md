# CLAUDE.md

> Lean router, loaded into every context. Says *when* to read a file, not what's in it.
> Project-agnostic rules (code reuse, doc hygiene) live in ~/.claude/CLAUDE.md.

## Project

mxCloudShare (Python 3.11+, uv-managed, hatchling-packaged) — CLI and SDK for the CloudShare REST API v3. Automates training environments, VMs, snapshots, classes, and students.

## Core rules (always apply)

- `make check` runs lint (ruff) + test (pytest) — run before considering a change complete.
- All tests run offline (mock `cloudshare.req`). The single integration test is skipped unless `CLOUDSHARE_API_ID` / `CLOUDSHARE_API_KEY` are exported.
- Companion docs (ARCHITECTURE.md, INTEGRATION.md, USER_GUIDE.md) are append-only in substance: update in the same change as the code that invalidates them.
- Tracked items (PROGRESS.md, OPEN_ISSUES.md, plans/README.md) use tables with fixed-status vocabulary; see each file's own Columns note.

## When to read what

Read the linked file **before** doing the matching work. Do not inline these here.

| If you are…                                    | Read              | Source of truth          |
|-------------------------------------------------|-------------------|--------------------------|
| Changing data flow, service boundaries, or deps | `ARCHITECTURE.md` | this file                |
| Touching an external API, auth, or integration  | `INTEGRATION.md`  | this file + provider     |
| Explaining features to an end user              | `USER_GUIDE.md`   | this file                |
| Checking recent work / handoff state            | `PROGRESS.md`     | append-only log          |
| Looking for known bugs or blocked work          | `OPEN_ISSUES.md`  | tracker (files mirror)   |
| Planning a non-trivial change, or looking for why a past one was shaped a certain way | `plans/README.md` | this dir |
| Looking for a CLOSED item (archived history) | **do not read** `*_ARCHIVE.md` — ask the user first | archives |

## Update rules

- `ARCHITECTURE.md`, `INTEGRATION.md`, `USER_GUIDE.md` — stable reference. Update only when the underlying design changes, in the same change as the change.
- `PROGRESS.md`, `OPEN_ISSUES.md`, `plans/README.md` — tracked items are recorded as **tables**, minimum columns `ID | Status | Description | Notes | Opened | Closed`. `Status` is one of `open` / `in-progress` / `blocked` / `watch (YYYY-MM-DD)` / `done` / `dropped`; `Closed` is set only for `done` / `dropped`, `—` otherwise. See each file's own Columns note.
- Those tables are **append-only in substance**: add rows at the end, never delete a row, reorder rows, or reword an existing `Description`. Advancing an item means editing its `Status` / `Notes` / `Closed` cells in place.
- `OPEN_ISSUES.md` — mirror of tracker. If they disagree, the tracker wins, and its IDs are the ones used here. Do not invent issues here.
- `PROGRESS_ARCHIVE.md`, `OPEN_ISSUES_ARCHIVE.md` — **never read these.** Closed (`done` / `dropped`, never `watch`) rows are swept into them at the start of a work session, verbatim and keeping the same IDs, so the working files stay light. Moving a closed row out is the only permitted removal from a working file: a move, not a delete. Archives are append-only; never edit or reorder an archived row. Do not open, grep or quote an archive unless the user explicitly asks about archived history.
- `plans/` — the plan FILES are write-once; a plan worth keeping gets promoted here explicitly (see `plans/README.md`), never auto-generated or silently edited after landing. Only the index table in `plans/README.md` is updated in place.