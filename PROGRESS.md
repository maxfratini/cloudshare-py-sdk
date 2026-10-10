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
| PRG-009 | done        | Live lifecycle test on 4-VM "Continuous Data Admin (Oracle)" + HTTP timeout fix | "Delphix Oracle Admin" does not exist; user picked `BPsheyiCWW0nuYPWKTQQsjFA2`. CLI `env-create` OK (~6 s, VMs `Loading from snapshot` then `Running`), `env-suspend` → all `Suspended` in ~4 s, `env-resume` → `Running` OK. VM `statusText` is `Running`, not `Ready` (`Ready` is the env-level status). Suspend/resume called while still loading are silently no-ops (rc 0, no output). Network dropped mid-run: `env-delete` then hung 15+ min because `urlopen` had no timeout → added 60 s (`Http.TIMEOUT_SECS`) + test. Env removed via SDK (`cs_env_delete`); account verified empty. Follow-up: PRG-010. | 2026-10-10 | 2026-10-10 | main/Sonnet 5.5 |
| PRG-010 | done        | `env-suspend` waits for VMs Running; visible warnings on skip/timeout | Root cause of the silent no-op: skip/timeout messages used `mxlogger.info`, below default level PRINT. Now `warning`. New `env_wait_vms_running`; `env_wait_condition` no longer spins to timeout on 0-VM envs. `env-delete` deliberately does not wait (API accepts it while loading); `env-resume` acts on Suspended envs, nothing to wait for. Live check on 0-VM env: suspend OK, 2nd suspend prints `Skipping ...: cannot be suspended`, delete OK; the 4-VM wait path is covered by unit tests only. Note: `mxlogger.warning` prints bare text without the `WARNING:` colored prefix (mxLogger instance has no handler; falls to logging's last-resort) — pre-existing, same for `mxlogger.error`. Fixed in PRG-011. | 2026-10-10 | 2026-10-10 | main/Sonnet 5.5 |
| PRG-011 | done        | Replace `mxLogger` with stdlib logging + RichHandler (stderr) | `mxLogger` kept handlers on an inner logger, so `mxlogger.info/debug` (77 call sites) printed nothing and `--logfile` got only `.print` — `--loglevel INFO/DEBUG` never worked. Now `mxLogging.setup_mxLogger()` configures the `mxcloudshare` package logger (idempotent): Rich handler on stderr (PRINT bare, others `LEVEL: msg`, markup only for `.print`), optional file handler; `getLogger()` is a plain `logging.Logger`, `requester.py` shares the handlers. Removed the debug line that would have logged `API_KEY`; `requester.py` DEBUG logs now redact `Authorization`. Nuitka standalone: 60336 → 60352 KB (+16 KB), compiled binary checked. Behaviour change: console messages (incl. `.print`) moved stdout → stderr. Request bodies are still logged unredacted at DEBUG. | 2026-10-10 | 2026-10-10 | main/Sonnet 5.5 |

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
