# PROGRESS — ARCHIVE

> ## ⚠ Do not read this file
>
> This is write-mostly history, kept out of context on purpose so `PROGRESS.md` stays light.
> **Agents must not open, grep, quote or summarise this file** unless the user explicitly asks
> about archived or historical work. If you think you need something in here, say so and ask —
> do not read it first and apologise later.
>
> Closed items (`done`, `dropped`) are swept here from `PROGRESS.md` at the start of a work
> session, **verbatim**: same columns, same IDs, never reworded, renumbered or merged. IDs are
> never reused after archiving. `watch` rows never arrive here: they are fixed but their rule is
> still active, so they stay in the working file where someone will notice if it is removed.
>
> Append-only and chronological. Never edit or reorder a row once it is here. If an archived
> item turns out to be unfinished, open a NEW row in `PROGRESS.md` referencing the archived ID.

| ID | Status | Description | Notes | Opened | Closed | Session |
|----|--------|-------------|-------|--------|--------|---------|

## Entry detail

Full verbatim text of archived items, in the same order as the table.
| PRG-001 | done        | Project review & plan created    | Comprehensive audit of cloudshare project; plan at plans/2026-10-07-cloudshare-review.md | 2026-10-07 | 2026-10-07 | nimbalyst-coach |
| PRG-002 | done        | Fix wrapper_cls.py bug (P1-1)    | Fixed by PRG-003's partial refactor: `.cs_get()` → `.get()`, `dct` → `new_dct` | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-003 | done        | Replace pandas with dict-flattener (P1-2) | Finished by fix-4: 8 ruff errors fixed, config wiring, make check green. pandas removed from deps/source. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-004 | done        | Add tests for mxcloudshare.py SDK (P1-3) | tests/test_mxcloudshare_sdk.py: 22 pre-existing-helpers + P2-1 auth refactor. tests/test_mxlogging.py (20), test_mxcyclopts.py (21), test_wrapper.py (19). All landed. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-005 | done        | API gap-closure plan executed   | PLAN-002 lanes L1–L7 + Phase 3 all done. Final: 74 cs_ helpers, ~63 CLI commands, 189 tests, make check green. From 16% → 100% endpoint reachable via CLI. | 2026-10-07 | 2026-10-07 | main/big-pickle |
| PRG-006 | done        | PLAN-001 execution (P2/P3/P4)   | 12/15 PLAN-001 items landed. P2-1/P3-2/P3-3/P3-4/P2-2/P2-3/P2-4/P3-1/P3-5/P3-6/P4-2/P4-3 done. P3-2/3/4 included --version, --dry-run, --json. P4-1 blocked (sandbox creds). mxCyclopts 9 test skips pre-existing (cyclopts v5 bug out of scope). | 2026-10-07 | 2026-10-07 | main/big-pickle |
