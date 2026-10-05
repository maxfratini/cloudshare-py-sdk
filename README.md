mxCloudShare
============
A [uv](https://docs.astral.sh/uv/)-managed CLI and SDK for the
[CloudShare](https://www.cloudshare.com) REST API v3, packaged with
[hatchling](https://hatch.pypa.io/) and compilable to standalone binaries with
[Nuitka](https://nuitka.net/).

Fork of the upstream [cloudshare-py-sdk](https://github.com/cloudshare/cloudshare-py-sdk)
(Apache 2.0), with the CLI layer added.


Install
-------
Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync                # create .venv and install everything
uv run mxcloudshare --help
```

Other ways to run it:

```bash
uv run python -m mxcloudshare --help     # as a module
uv tool install .                        # global `mxcloudshare` command
uv run mxcloudshare shell                # interactive shell
```


Credentials
-----------
Resolved in this order:

1. the file passed with `--keyfile`
2. `CLOUDSHARE_API_ID` / `CLOUDSHARE_API_KEY` environment variables
3. `./cloudshare.env`

`cloudshare.keys` and `cloudshare.env` are gitignored — never commit them.


Usage
-----
The command name comes **before** the options, because the CLI is built with
[cyclopts](https://cyclopts.readthedocs.io/):

```bash
mxcloudshare env-show-all --outformat table --tablewidth 120
mxcloudshare env-suspend --envid <env-id> --outformat table
mxcloudshare env-resume  --envid <env-id> --outformat table
mxcloudshare env-create  --blueprint-id <bp-id> --name lab --count 5
mxcloudshare class-list  --fields id,name --pattern '^Lab'
```

`--outformat` accepts `json` (default), `table`, `card`, or `csv`. Add
`--loglevel DEBUG` for detail, `--logfile <path>` to also write to disk.

The `env-*.sh` wrappers in the repo root are thin shortcuts around the above.


Using the SDK directly
----------------------
```python
from mxcloudshare.cloudshare import req

res = req(hostname="use.cloudshare.com",
          method="GET",
          path="envs",
          apiId="Your API ID",
          apiKey="Your API Key")
if res.status // 100 != 2:
    raise Exception(res.status, res.content)
```

The higher-level helpers live in `mxcloudshare.mxcloudshare`:

```python
from mxcloudshare import mxcloudshare as cs

cs.cs_set_auth_keys(api_id, api_key)
envs = cs.cs_env_get_all()
```


Development
-----------
```bash
make setup    # uv sync --all-groups
make test     # pytest
make lint     # ruff check
make check    # lint + test
make help     # list all targets
```

Tests run entirely offline. The single integration test
(`tests/test_integration.py`) is skipped unless `CLOUDSHARE_API_ID` and
`CLOUDSHARE_API_KEY` are exported.


Building binaries
-----------------
`make dist` produces a standalone folder for the **host** OS; the executable
lands in `dist/main.dist/mxcloudshare` (`mxcloudshare.exe` on Windows).

```bash
make dist           # standalone folder (default)
make build-onefile  # single self-extracting executable
make dist-bundle    # macOS .app bundle
```

Build options are the `# nuitka-project` comments at the top of `main.py`,
which is also what lets them vary per OS. `main.py` exists purely as Nuitka's
main program — Nuitka compiles a script path and cannot compile
`python -m mxcloudshare` directly.

> **Nuitka does not cross-compile.** A macOS binary must be built on macOS, a
> Linux binary on Linux, and so on. `.github/workflows/build.yml` runs the
> matrix for you and uploads `dist/main.dist/**` per platform.

The pandas dependency makes the binary large (~130 MB standalone, since numpy
and pandas ship as compiled extension modules). `pandas.json_normalize` is used
only to flatten API responses into tables for `rich`; replacing it with a small
dict-flattening helper would cut the binary by roughly an order of magnitude if
size matters.

Distribution note: Linux artifacts need `patchelf` installed
(`apt-get install patchelf`) so Nuitka can rewrite the shared libraries it
bundles.


Let's Encrypt certificates
--------------------------
If TLS verification fails on an older OS, update the root certificates:

- <https://letsencrypt.org/certs/isrgrootx1.der>
- <https://letsencrypt.org/certs/isrg-root-x2.der>
- <https://letsencrypt.org/certs/lets-encrypt-r3.der>

More info: <https://letsencrypt.org/certificates/>