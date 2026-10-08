# CloudShare Project Review & Plan

**Created:** 2026-10-07
**Status:** open
**Source:** nimbalyst-coach review session

---

## Summary

mxCloudShare (v0.2.0) is a functional CLI/SDK for CloudShare REST API v3, but has significant gaps in docs, tests, code quality, and dependencies. This plan prioritizes high-impact improvements first.

## Current State

| Area | Status |
|------|--------|
| Core CLI/SDK | ✅ Working — env, class, blueprint, policy, VM ops |
| Tests | ⚠️ Partial — auth, requester, CLI covered; SDK layer & wrappers untested |
| Docs | ❌ Empty templates only (ARCHITECTURE.md, INTEGRATION.md, USER_GUIDE.md, CLAUDE.md) |
| Binary size | ❌ ~130 MB due to pandas+numpy |
| Known bugs | ❌ wrapper_cls.py:95 — `cs_get()` called on dict (AttributeError) |

## Prioritized Plan

### Phase 1 — Stability (P0)

| ID | Work | Why |
|----|------|-----|
| P1-1 | Fix `wrapper_cls.py:95` — `dct['itemsCart'][0].cs_get('snapshotId')` → `.get('snapshotId')` | Latent bug, dead code path |
| P1-2 | Replace `pd.json_normalize` with small dict-flattener | Eliminates pandas (~130 MB binary), major DX win |
| P1-3 | Add tests for `mxcloudshare.py` SDK layer (~20 functions) | Core business logic has zero test coverage |

### Phase 2 — Quality (P1)

| ID | Work | Why |
|----|------|-----|
| P2-1 | Remove global mutable state (`globalconf` dict, module globals) | Thread-unsafe, test-pollution risk |
| P2-2 | Unify `wrapper.py` (functional) and `wrapper_cls.py` (OOP) | Duplicated logic, two styles |
| P2-3 | Implement CSV output (currently `>>> Csv not implemented yet <<<`) | Acknowledged gap, simple to fix |
| P2-4 | Deduplicate `cli.py` field-filtering logic (env_get_info vs env_get_vms_info) | DRY violation |

### Phase 3 — DX & Features (P2)

| ID | Work | Why |
|----|------|-----|
| P3-1 | Fill in all stub docs (ARCHITECTURE.md, INTEGRATION.md, USER_GUIDE.md, CLAUDE.md) | Project is undocumented |
| P3-2 | Add `--version` flag | Basic CLI completeness |
| P3-3 | Add `--dry-run` to suspend/delete/resume | Safety for destructive ops |
| P3-4 | Add `--json` input support for env_create / class_create | Complex payloads |
| P3-5 | Clean up `deleteExpiredClasses.py` example (uses raw requests+typer, not SDK) | Consistency |
| P3-6 | Add async/polling with progress bars for long-running ops | UX improvement |

### Phase 4 — Robustness (P3)

| ID | Work | Why |
|----|------|-----|
| P4-1 | Add integration test suite (sandbox account) | Only 1 skipped integration test |
| P4-2 | Add end-to-end CLI binary smoke test | CI has minimal smoke test |
| P4-3 | Add tests for logging (`mxLogging.py`) and cyclopts utils (`mxCyclopts.py`) | ~400 lines untested |

## Dependencies

- P1-2 (pandas removal) unblocks P1-3 test work on DataFrame output
- P2-1 (global state removal) unblocks P2-2 unification
- P3-1 docs can proceed independently anytime

## Decisions Needed

1. **Keep `wrapper.py` (functional) or `wrapper_cls.py` (OOP)?** — Recommend functional; OOP adds statefulness without clear benefit for a CLI tool.
2. **Dict-flattener approach?** — Small custom function or `pyyaml` safe_load for nested dicts?
3. **Replace `cyclopts` with `click` or `typer`?** — Lower priority; current framework works.
