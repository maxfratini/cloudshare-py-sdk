# API Gap Closure — Implementation Plan

**Created:** 2026-10-07
**Status:** open
**Source:** gap analysis mxcloudshare vs CloudShare REST API v3 (`docs.cloudshare.com/rest-api/v3`)
**Audience:** specialist subagents (@librarian / @fixer / @oracle). Each lane below is written to be
handed to a fresh-context agent: exact file paths, endpoint paths, naming rules, acceptance criteria.

---

## Goal

Close the highest-value coverage gaps between mxcloudshare and the documented CloudShare v3 API.
Current state: **14 of ~86** documented endpoints have typed SDK helpers (~16%); the CLI exposes
16 commands. Phase 1 targets lifecycle/snapshots/VM ops/project paths, Phase 2 training, Phase 3
the long tail.

## Non-goals (owned elsewhere — do not touch)

| Item | Owner |
|------|-------|
| pandas → dict-flattener (cli.py `print_results`/`df_to_table`) | PRG-003 |
| `wrapper_cls.py:95` bug + wrapper unification | PRG-002 / PLAN-001 P2-1, P2-2 |
| CSV output formatter | PLAN-001 P2-3 |
| Stub docs fill-in (ARCHITECTURE/INTEGRATION/USER_GUIDE/CLAUDE) | PLAN-001 P3-1 |
| Existing SDK-layer test file `tests/test_mxcloudshare.py` | PRG-004 session |
| CloudShare API v4 (Accelerate platform) | out of scope entirely |

## Fixed decisions (do not re-litigate)

- **D1 — Naming.** SDK helpers: `cs_<resource>_<verb>(...)` in `mxcloudshare/mxcloudshare.py`.
  CLI commands: `<resource>-<verb>` registered with `@cs_app.command()` in `mxcloudshare/cli.py`
  (cyclopts style, command name before options).
- **D2 — Plumbing.** New helpers call the existing `cs_get` / `cs_post` / `cs_put` / `cs_delete`
  helpers only — never `cloudshare.req` directly. Error handling stays in `cs_request`.
- **D3 — Legacy paths stay.** `cs_blueprint_get_all()` (`/blueprints`) and `cs_policy_get_all()`
  (`/policies`) are undocumented but in production use. Keep them working unchanged; ADD
  project-scoped official-path helpers alongside. Do not change any existing function signature
  (24 tests in `tests/test_mxcloudshare.py` depend on them).
- **D4 — `POST /envs/actions/create` stays as-is.** Official docs say `POST /envs`; the legacy
  action path works today. Changing it is a separate risk decision, not part of this plan.
- **D5 — New tests go in a NEW file** `tests/test_mxcloudshare_api_gaps.py`. Pattern: mock
  `cloudshare.req` with `unittest.mock` as in `tests/test_mxcloudshare.py`
  (`make_mock_response`). Offline only — no real credentials, no network.
- **D6 — Validation owner: every lane runs `make check`** (ruff + pytest) and reports the result
  before being considered done. Orchestrator reconciles terminal results.
- **D7 — File boundaries.** Lanes may only write the files listed in their scope. In particular:
  never edit `wrapper.py` / `wrapper_cls.py`, never edit `print_results` / `df_to_table` /
  `show_results` in `cli.py`, never edit `tests/test_mxcloudshare.py`.

## Endpoint reference — Phase 1 (docs.cloudshare.com/rest-api/v3/…)

| Method | Path | New helper (D1) |
|--------|------|-----------------|
| PUT | `envs/actions/extend` | `cs_env_extend` |
| PUT | `envs/actions/revert` | `cs_env_revert` |
| PUT | `envs/actions/postponeinactivity` | `cs_env_postpone_inactivity` |
| PATCH | `envs` | via upgraded `cs_api_call` |
| GET | `snapshots/ID` | `cs_snapshot_get` |
| GET | `snapshots/actions/getforenv` | `cs_snapshot_get_for_env` |
| POST | `snapshots/actions/takesnapshot` | `cs_snapshot_take` |
| PUT | `snapshots/actions/markdefault` | `cs_snapshot_mark_default` |
| PUT | `vms/actions/reboot` | `cs_vm_reboot` |
| PUT | `vms/actions/revert` | `cs_vm_revert` |
| DELETE | `vms/ID` | `cs_vm_delete` |
| PUT | `vms/actions/editvmhardware` | `cs_vm_edit_hardware` |
| GET | `vms/actions/getremoteaccessfile` | `cs_vm_get_remote_access_file` |
| GET | `projects` | `cs_project_get_all` |
| GET | `projects/ID/blueprints` | `cs_project_blueprints_get_all` |
| GET | `projects/ID/policies` | `cs_project_policies_get_all` |

Doc slugs for L1 fetch (prefix `https://docs.cloudshare.com/rest-api/v3/`):
`environments/envs/put-api-v3-envs-actions-extend/`, `…-revert/`,
`…-postponeinactivity/`, `environments/envs/patch-envs/`,
`environments/snapshots/actions-takesnapshot/`, `…getforenv/`, `…markdefault/`,
`environments/snapshots/get-id/`, `environments/vms/put-api-v3-vms-actions-reboot/`,
`…-revert/`, `…-editvmhardware/`, `environments/vms/delete-api-v3-vms-id/`,
`environments/vms/get-api-v3-vms-actions-getremoteaccessfile/`,
`project/projects/get-api-v3-projects/`, `project/blueprints/get-api-v3-projects-id-blueprints/`,
`project/policies/get-api-v3-projects-id-policies/`.

---

## Phase 1 — Lifecycle, snapshots, VM ops, project paths (P0)

### L1 — Endpoint spec digest · @librarian · background · no deps

- **Scope:** web research only, zero file writes.
- Fetch the Phase-1 doc pages above. For each endpoint return: exact method+path, query/body
  parameter names, types, required/optional, response fields worth asserting in tests.
- **Deliverable:** one markdown spec table in the final message; orchestrator pastes it verbatim
  into L2's prompt.
- **Validation:** orchestrator checks completeness against the table above.

### L2 — SDK helpers · @fixer · background · depends on L1

- **Files owned:** `mxcloudshare/mxcloudshare.py`, `tests/test_mxcloudshare_api_gaps.py` (new).
- Implement every helper in the Phase-1 table per L1's spec (params/payloads exactly as docs say).
- Upgrade `cs_api_call`: new signature `cs_api_call(method, path, payload=None, queryParams=None)`
  supporting **PATCH** and **OPTIONS**, and passing `queryParams` through on GET/DELETE (today GET
  silently drops them). Keep backward compatibility with the existing 4-positional-arg calls.
- Follow existing file style: one-line docstrings, `cs_` prefix, no new dependencies.
- **Acceptance:** `make check` green; ≥1 test per new helper asserting method, path, and
  query/body mapping; no pre-existing function signature or behavior changed (D7).

### L3 — CLI commands · @fixer · background · depends on L2

- **Files owned:** `mxcloudshare/cli.py`, `tests/test_cli.py` (append new test classes only).
- New commands, all following the `env_suspend` pattern (`Annotated` params, `initializeApp`,
  `mxlogger`, `print_results`, `common: mxCommonOpts | None`):
  - `env-extend`, `env-revert`, `env-postpone`
  - `snapshot-take`, `snapshot-list` (by `--envid`), `snapshot-mark-default`
  - `vm-reboot`, `vm-revert`, `vm-delete`, `vm-hardware` (payload as `--payload` JSON string),
    `vm-remote-access`
  - **`api-call <METHOD> <PATH>`** with `--query k=v` (repeatable) and `--body` JSON — generic
    escape hatch so the CLI can reach any endpoint, not just typed ones. Uses `cs_api_call`.
  - `blueprint-list` / `policy-list`: add optional `--project-id`; when given use the new
    project-scoped helpers (D3), otherwise keep current behavior.
- Reuse `env_wait_condition` polling only where the spec documents a status transition
  (revert); do not invent polling for fire-and-forget actions.
- **Acceptance:** `make check` green; every command's `--help` renders; at least one CLI test per
  command group following `test_cli.py` conventions.

### L4 — Oracle review · @oracle · background · depends on L3

- Review the full Phase-1 diff (no writes): correctness vs official docs, D1–D7 compliance,
  naming consistency, test adequacy, and anything that flattens existing structure.
- **Deliverable:** findings classified `must-fix` / `nice-to-have`. `must-fix` items go to a
  follow-up @fixer lane before L5.

### L5 — Docs · @fixer · background · depends on L4

- **Files owned:** `README.md` only (add the new commands to the Usage section and the generic
  `api-call` example). Do not fill stub docs — that is PLAN-001 P3-1's job.
- Orchestrator reviews the copy afterwards.

**Phase 1 exit:** coverage ≈ 29/86 typed helpers (~34%), CLI ~28 commands + generic `api-call`
reaching 100% of endpoints from the CLI.

---

## Phase 2 — Training & class actions (P1)

Runs serially after Phase 1 (same two hot files).

### L6 — Training spec digest · @librarian · background · depends on L5

Endpoints: `class/actions/sendinvitations`, `class/actions/SuspendAllEnvironments`,
`class/actions/DeleteAllEnvironments`, `class/sponsoredlink`, `class/disablesponsoredlink`,
`Class/ID/Students/actions/ResumeEnvironmentForStudent`, `class/actions/getdetailed`,
`class/actions/countries`, `class/actions/customfields`, students CRUD
(`GET/POST/PUT/DELETE class/ID/students[...]`), instructors CRUD (`POST/DELETE instructors/ID`,
`GET instructors/class`). Doc slugs under
`https://docs.cloudshare.com/rest-api/v3/training/…`.

### L7 — Training implementation · @fixer · background · depends on L6

- **Files owned:** `mxcloudshare/mxcloudshare.py`, `mxcloudshare/cli.py`,
  `tests/test_mxcloudshare_api_gaps.py`, `tests/test_cli.py` (append-only).
- Helpers: `cs_class_*` extensions + `cs_student_*` + `cs_instructor_*` per D1/D2.
- CLI: `class-sendinvitations`, `class-suspend-all`, `class-delete-all`,
  `class-sponsoredlink`, `student-list/get/create/update/delete`, `instructor-list/create/delete`.
- `examples/login_as_students.py` may keep using raw `req()` — not in scope.
- **Acceptance:** `make check` green; same test rules as L2/L3; D7 boundaries respected.

**Phase 2 exit:** coverage ≈ 44/86 (~51%).

---

## Phase 3 — Long tail (P2, optional, dispatch only if requested)

One serial batch per group, spec-then-fix pattern (same as L1→L2):

| Batch | Endpoints | Notes |
|-------|-----------|-------|
| Webhooks | 4 (GET/GET id/POST/DELETE) | event automation |
| Permalinks | 2 (POST/GET) | snapshot sharing |
| Users/Teams/Invitations | 9 incl. 2 OPTIONS | `inviteprojectmember`, `invitetopoc`, `sponsoredlinks`, `teams`, `getloginurl`, `RemoveUserRole` |
| Utilities | 3 (ping, regions, timezones) | quick wins |
| Analytics / Guided Journey / SharedEnv / Public Clouds | 8 | read-mostly |

Each batch: @librarian spec → @fixer (same 4 files) → `make check` → @oracle spot-review only if
the batch touches >3 files.

---

## Dispatch order (summary)

```
L1 librarian ──► L2 fixer ──► L3 fixer ──► L4 oracle ──► L5 fixer ──► [Phase 1 done]
                                                                            │
                                                          L6 librarian ──► L7 fixer ──► [Phase 2 done]
                                                                              │
                                                          Phase 3 batches (on request)
```

- All lanes run **background**; orchestrator reconciles on terminal results, never polls.
- No two write-capable lanes are ever in flight at once (they share `mxcloudshare.py`/`cli.py`);
  L1 is the only lane that can overlap a write lane.

## Risk register

| Risk | Mitigation |
|------|------------|
| Legacy `/blueprints`, `/policies`, `/envs/actions/create` paths undocumented upstream | D3/D4: keep, add official-path alternatives; flag `watch` in OPEN_ISSUES after Phase 1 lands |
| Another session editing `cli.py`/`mxcloudshare.py` concurrently | D7 file boundaries; orchestrator diffs before dispatching each write lane |
| Doc payload details wrong (L1 digest stale/missed page) | L2 asserts against official doc slugs listed here; L4 re-checks vs docs |
