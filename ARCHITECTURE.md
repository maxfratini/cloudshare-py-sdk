# ARCHITECTURE

> Read before changing data flow, service boundaries, or dependencies.
> Stable reference. Update in the same change as any structural change.

## Overview

mxCloudShare is a CLI and SDK for automating the CloudShare REST API v3. It is managed with [uv](https://docs.astral.sh/uv/), packaged with [hatchling](https://hatch.pypa.io/), and compilable to standalone binaries with [Nuitka](https://nuitka.net/). The project is a fork of the upstream [cloudshare-py-sdk](https://github.com/cloudshare/cloudshare-py-sdk) (Apache 2.0 license), with a full CLI layer added on top of the original SDK wrappers. The system has four layers: a CLI layer that defines commands and output formatting, a typed SDK layer that provides named helpers for each API resource, an HTTP layer that handles request signing and transport, and a utilities layer for logging and Cyclopts framework support. The CLI reaches the CloudShare API through this pipeline: a CLI command calls an SDK helper, which calls the HTTP requester, which issues a signed request to `https://use.cloudshare.com/api/v3/`.

## Components

| Component | Responsibility | Location |
|-----------|----------------|----------|
| CLI layer | Command definitions (Cyclopts `App`), argument parsing via `mxCommonOpts`, app initialization (`initializeApp`), output formatting (`print_results` / `show_results` / `print_as_table`), and polling logic (`env_wait_condition`) | `mxcloudshare/cli.py` (entry point: `main()` exports to `pyproject.toml` as `mxcloudshare.cli:main`; also `main.py` as Nuitka launcher) |
| Typed SDK | Named helpers (`cs_<resource>_<verb>`) wrapping the HTTP layer; generic escape hatch `cs_api_call`; auth key management via `cs_set_auth_keys` | `mxcloudshare/mxcloudshare.py` |
| HTTP layer | Raw request construction (`Requester._build_url`, `_build_headers`), CS-SHA1 HMAC authentication (`authentication_parameter_provider.py`, `hmacer.py`, `token_generator.py`), URL-encoded query parameter serialization, JSON response parsing | `mxcloudshare/cloudshare/` — `requester.py`, `http.py` (stdlib `urllib.request`), `ioc.py` (DI wiring), `authentication_parameter_provider.py`, `hmacer.py`, `token_generator.py` |
| Legacy wrappers | Two parallel (unified) wrappers providing name-to-ID resolution plus higher-level workflows like `create_env_from_bp_using_names`. **Note:** these are the original upstream SDK modules and are *not* used by the modern CLI/SDK path — the CLI calls `mxcloudshare.py` helpers, which call `cloudshare.req` directly. | `mxcloudshare/cloudshare/wrapper.py` (functional), `mxcloudshare/cloudshare/wrapper_cls.py` (OOP `Wrapper` class) |
| Utilities | Custom logging (`mxLogger` with a `PRINT` level at 25 and Rich console output), Cyclopts framework extensions (`CommonOpts` base class, `mxCycloptsApp` with `command_with_commonopts`) | `mxcloudshare/mxutils/mxLogging.py`, `mxcloudshare/mxutils/mxCyclopts.py` |

## Data flow

A CLI invocation flows through four stages:

1. **CLI command** — Cyclopts parses the command name and arguments. Every command has a `common: mxCommonOpts | None` parameter that captures `--outformat`, `--tablewidth`, `--keyfile`, `--loglevel`, and `--logfile`. The command calls `initializeApp(common)`.

2. **`initializeApp`** — Sets up the `mxLogger` (logging level and optional file), calls `loadKeys()` to resolve CloudShare credentials (priority: `--keyfile` argument > environment variables `CLOUDSHARE_API_ID`/`CLOUDSHARE_API_KEY` > `./cloudshare.env` file), stores them in an `AppConfig` dataclass, and propagates them into the SDK globals via `cs.cs_set_auth_keys(api_id, api_key)`.

3. **SDK helper** — The command calls one or more `cs_*` helper functions from `mxcloudshare/mxcloudshare.py`. Each helper constructs an endpoint path, calls `cs_get`/`cs_post`/`cs_put`/`cs_delete` (which all delegate to `cs_request`), and returns parsed JSON. For commands that involve status transitions (suspend, resume, delete, revert), the CLI polls with `env_wait_condition`, which calls `cs.get_vms(envId)` in a loop until VM `statusText` matches the target state or a retry limit is reached.

4. **`cs_request`** — Calls `cloudshare.req(hostname="use.cloudshare.com", ...)`, which creates a `Requester` instance from `ioc.py`, builds the full URL (`https://use.cloudshare.com/api/v3/<path>`), adds a `cs_sha1` Authorization header computed from the API key, issues the HTTP request via stdlib `urllib.request`, and returns the JSON-parsed response. The SDK raises an exception if the response status is not 2xx.

5. **Output formatting** — The command passes the returned data to `print_results(data, config)`, which dispatches on `config.outputformat`: `json` (default, using `rich.print_json`), `table` (via `show_results` which builds a Rich `Table`), `card` (key-value pairs for single-item results, falls back to table for multi-item), or `csv` (stdlib `csv` writer quoting all fields).

## Key decisions

- **Cyclopts CLI framework** — Cyclopts was chosen (over Click or Typer) for its command-name-before-options convention and its Annotation-driven argument parsing. This means `mxcloudshare env-show-all --outformat table`, not `mxcloudshare --outformat table env-show-all`. The existing `mxCyclopts.py` module provides a `CommonOpts` base class and an `mxCycloptsApp` subclass with a `command_with_commonopts` decorator, but the CLI currently uses the simpler pattern of a `mxCommonOpts` dataclass with `@Parameter(name="*")` on every command signature instead.
- **Typed SDK helpers (`cs_<resource>_<verb>`)** — Named helpers make the 46 most common endpoints discoverable through function signatures and docstrings, while a generic `cs_api_call(method, path, payload, queryParams)` escape hatch covers every other documented endpoint. This avoids needing full SDK coverage before the CLI is useful.
- **Legacy API paths retained** — The upstream SDK used undocumented endpoints like `/blueprints`, `/policies`, and `/envs/actions/create`. These are kept working unchanged alongside new official-path helpers to avoid breaking existing scripts that depend on them (see plans/2026-10-07-api-gap-closure.md decisions D3/D4).
- **No pandas** — The original code used `pd.json_normalize` for table output. A custom `_flatten_dict`/`_dict_to_rows` pair replaced it, eliminating the pandas dependency and reducing the standalone binary size by approximately 130 MB.
- **stdlib HTTP only** — The HTTP layer uses Python's `urllib.request` with no external HTTP library (no `requests`, no `httpx`). The CS-SHA1 HMAC authentication scheme is implemented in-house (`hmacer.py`, `token_generator.py`, `authentication_parameter_provider.py`).
- **Stateless initialization** — `initializeApp` returns an `AppConfig` dataclass rather than mutating a global dictionary. The SDK globals (`_apiID`, `_apiKey`) in `mxcloudshare.py` remain module-level but are set once at initialization time rather than read from a mutable `globalconf`.

## Constraints & invariants

- Python 3.11+ is required (f-strings, `Annotated`, `list[str]` type hints).
- Tests run entirely offline — every test mocks `cloudshare.req` with `unittest.mock`. The single integration test (`tests/test_integration.py`) is skipped unless real credentials are exported.
- The Nuitka binary launcher (`main.py`) exists solely because Nuitka compiles a script path and cannot compile `python -m mxcloudshare`. It is intentionally not part of the wheel.
- Nuitka does not cross-compile — each target OS needs its own build machine (the GitHub Actions matrix handles this via `.github/workflows/build.yml`).
- The two legacy wrapper modules (`wrapper.py` and `wrapper_cls.py`) are *not* part of the CLI data path. They are retained for backward compatibility with any external code importing `mxcloudshare.cloudshare.wrapper` directly. The CLI and modern SDK only use `cloudshare.req` from `cloudshare/__init__.py`.