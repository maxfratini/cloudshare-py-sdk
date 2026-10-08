# USER GUIDE

> Written for **end users**, not agents. Read only when explaining features or writing user-facing help.

## What this does

mxCloudShare is a command-line tool for automating the CloudShare training and demo platform. You can create, manage, suspend, delete, and inspect environments and their VMs, work with snapshots, manage classes and students, list blueprints and policies, create webhooks and permalinks, and make arbitrary API calls to any CloudShare REST API v3 endpoint. Output is available in JSON, table, card, or CSV format.

## Getting started

### Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- A CloudShare account with API credentials

### Installation

```bash
git clone <this-repo>
cd cloudshare
uv sync               # create .venv and install dependencies
```

Run commands as:

```bash
uv run mxcloudshare <command> [options]
uv run python -m mxcloudshare <command> [options]
```

For an interactive shell:

```bash
uv run mxcloudshare shell
```

### Setting credentials

Authentication requires two values: `CLOUDSHARE_API_ID` and `CLOUDSHARE_API_KEY`. The tool resolves them in this order:

1. **`--keyfile` / `-k`** — A path to a `.env` file containing the keys:
   ```
   CLOUDSHARE_API_ID=your-id
   CLOUDSHARE_API_KEY=your-key
   ```

2. **Environment variables** — If no `--keyfile` is given:
   ```bash
   export CLOUDSHARE_API_ID=your-id
   export CLOUDSHARE_API_KEY=your-key
   ```

3. **`./cloudshare.env`** — If neither of the above is found, the tool looks for a `cloudshare.env` file in the current directory.

If no credentials are found, the tool exits with instructions. The files `cloudshare.keys` and `cloudshare.env` are gitignored — never commit them.

## Common flags

Every command accepts these options:

| Flag | Default | Description |
|------|---------|-------------|
| `--outformat` | `json` | Output format: `json`, `table`, `card`, or `csv` |
| `--tablewidth` | `80` | Column width for table output |
| `--keyfile` / `-k` | — | Path to auth keys file |
| `--loglevel` | `PRINT` | Logging level: `PRINT`, `INFO`, `DEBUG`, `WARNING`, `ERROR` |
| `--logfile` | — | Path to write a log file (appended) |

The command name comes **before** options — this is a Cyclopts convention:
```
mxcloudshare env-show-all --outformat table --tablewidth 120
```

## Environment lifecycle

### Show all environments

```bash
mxcloudshare env-show-all [--outformat table]
```

Lists every environment with its index, id, name, status, and owner email.

### Show environment details

```bash
mxcloudshare env-get-info <env-id> [--field name,status] [--all]
```

Shows full details for a single environment. Use `--field` to select specific attributes (repeatable). Use `--all` to list all available attribute names without showing data.

### Show VM information

```bash
mxcloudshare env-get-vms-info <env-id> [--field name,statusText] [--all]
```

Lists every VM in an environment with its properties. `--field` and `--all` work the same as `env-get-info`.

### Suspend an environment

```bash
mxcloudshare env-suspend --envid <env-id> [--envid <env-id-2> ...]
```

Suspends one or more environments. Only environments in "Ready" status can be suspended. The tool polls every 6 seconds (up to 20 retries) until every VM reports "Suspended" status.

### Resume an environment

```bash
mxcloudshare env-resume --envid <env-id> [--envid <env-id-2> ...]
```

Resumes one or more suspended environments. Only environments in "Suspended" status can be resumed. Polls until VMs report "Running".

### Delete an environment

```bash
mxcloudshare env-delete --envid <env-id> [--envid <env-id-2> ...]
```

Deletes one or more environments. Already-deleted environments are skipped. Polls until VMs report "Deleted".

### Extend an environment

```bash
mxcloudshare env-extend --envid <env-id> [--envid <env-id-2> ...]
```

Extends the duration of one or more environments. This is a fire-and-forget action — no polling.

### Revert an environment to a snapshot

```bash
mxcloudshare env-revert --envid <env-id> [--snapshot-id <snap-id>]
```

Reverts an environment to its default snapshot, or to the specified snapshot. Polls until VMs report "Ready".

### Postpone inactivity timeout

```bash
mxcloudshare env-postpone --envid <env-id> [--envid <env-id-2> ...]
```

Postpones the inactivity timeout for one or more environments. Fire-and-forget.

## Snapshots

### Take a snapshot

```bash
mxcloudshare snapshot-take <env-id> <snapshot-name> [--set-as-default] [description]
```

Creates a snapshot of an environment. Optionally set it as the default snapshot for the blueprint.

### List snapshots

```bash
mxcloudshare snapshot-list <env-id>
```

Lists all snapshots for an environment.

### Mark a snapshot as default

```bash
mxcloudshare snapshot-mark-default <snapshot-id>
```

Marks an existing snapshot as the default for its blueprint.

## VM operations

### Reboot a VM

```bash
mxcloudshare vm-reboot --vmid <vm-id> [--vmid <vm-id-2> ...]
```

Reboots one or more VMs. Fire-and-forget.

### Revert a VM to a snapshot

```bash
mxcloudshare vm-revert --vmid <vm-id> [--snapshot-id <snap-id>]
```

Reverts a VM to a snapshot. Fire-and-forget.

### Delete a VM

```bash
mxcloudshare vm-delete --vmid <vm-id> [--vmid <vm-id-2> ...]
```

Deletes one or more VMs. Fire-and-forget.

### Edit VM hardware

```bash
mxcloudshare vm-hardware <vm-id> '{"numCpus": 4, "memorySizeMBs": 8192}'
```

Updates CPU cores, memory (MB), or disk size (GB) on a VM. The payload is a JSON string.

### Get remote access file

```bash
mxcloudshare vm-remote-access <vm-id> [--desktop-width 1280] [--desktop-height 720]
```

Gets remote access connection details for a VM, optionally specifying desktop resolution.

## Classes and training

### List classes

```bash
mxcloudshare class-list --fields id,name --pattern '^Lab'
```

Lists all classes. Use `--fields` (comma-separated) to control which attributes are shown. Use `--pattern` (regex) to filter by class name.

### Show all classes

```bash
mxcloudshare class-show-all
```

Shows every class with all available attributes.

### Get class details

```bash
mxcloudshare class-get <class-id>
```

Shows the name of a specific class.

### Get detailed class info

```bash
mxcloudshare class-detailed <class-id>
```

Returns comprehensive class information including student and environment details.

### Create classes

```bash
mxcloudshare class-create <blueprint-id> [--policy-id <id>] [--name MyClass] [--count 3]
```

Creates one or more classes from a blueprint. When `--count` is greater than 1, names are suffixed with `-1`, `-2`, etc.

### Clone a class

```bash
mxcloudshare class-clone <class-id> [--count 2] [--name-suffix "-clone"]
```

Clones an existing class by reading its blueprint and policy and creating new classes with the same configuration.

### Suspend or resume classes by pattern

```bash
mxcloudshare class-setstatus <regex-pattern> [ACTIVE|SUSPENDED] [--by-id]
```

Finds classes matching the regex pattern (by name, or by ID with `--by-id`) and sets their status to ACTIVE or SUSPENDED.

### Delete classes by pattern

```bash
mxcloudshare class-delete <regex-pattern> [--by-id]
```

Deletes classes matching the regex pattern. Already-deleted classes are skipped.

### Send invitations to students

```bash
mxcloudshare class-sendinvitations <class-id> --student-id <sid> [--student-id <sid-2> ...] [--is-multiple true]
```

Sends invitations to specific students in a class. Defaults to sending as multiple invitations.

### Suspend or delete all environments in a class

```bash
mxcloudshare class-suspend-all <class-id>
mxcloudshare class-delete-all <class-id>
```

Bulk operations on every environment in a class.

### Manage sponsored links

```bash
mxcloudshare class-sponsoredlink <class-id> <student-email> --action create [--first-name ...] [--last-name ...] [--pre-register]
mxcloudshare class-sponsoredlink <class-id> <student-email> --action disable [--unregister-student]
```

Creates or disables a sponsored registration link for a student.

### Resume a student's environment

```bash
mxcloudshare class-resume-student <class-id> --student-id <sid> [--student-id <sid-2> ...]
```

Resumes the environment for specific students in a class.

### Get countries and custom fields for registration

```bash
mxcloudshare class-countries
mxcloudshare class-custom-fields
```

Lists countries and custom fields available for class registration forms.

### Guided journey analytics

```bash
mxcloudshare class-guided-journey <class-id>
mxcloudshare student-guided-journey <student-id>
```

Gets guided journey (training progress) data for a class or individual student.

## Students

| Command | Description |
|---------|-------------|
| `mxcloudshare student-list <class-id>` | List all students in a class |
| `mxcloudshare student-get <class-id> <student-id>` | Get a specific student |
| `mxcloudshare student-create <class-id> <email> [--first-name ...] [--last-name ...]` | Create a student |
| `mxcloudshare student-update <class-id> <student-id> '<json>'` | Update a student (payload as JSON) |
| `mxcloudshare student-delete <class-id> <student-id>` | Delete a student |

## Instructors

| Command | Description |
|---------|-------------|
| `mxcloudshare instructor-list [--class-id <id>]` | List all instructors, optionally filtered by class |
| `mxcloudshare instructor-create <vup-id> <class-id> [--send-invite-now] [--disable-env-creation]` | Add an instructor to a class |
| `mxcloudshare instructor-delete <instructor-id>` | Remove an instructor |

## Blueprints and policies

### List blueprints

```bash
mxcloudshare blueprint-list [--project-id <id>] [--field id,name] [--all]
```

Lists all blueprints, or blueprints scoped to a project when `--project-id` is given. `--field` and `--all` work as with other list commands.

### List policies

```bash
mxcloudshare policy-list [--project-id <id>] [--field id,name] [--all]
```

Lists all policies, or policies scoped to a project when `--project-id` is given.

## Webhooks

| Command | Description |
|---------|-------------|
| `mxcloudshare webhook-list` | List all webhooks |
| `mxcloudshare webhook-get <id>` | Get webhook details |
| `mxcloudshare webhook-create <url> <event>` | Create a webhook |
| `mxcloudshare webhook-delete <id>` | Delete a webhook |

## Permalinks

| Command | Description |
|---------|-------------|
| `mxcloudshare permalink-create <snapshot-id>` | Create a permalink for a snapshot |
| `mxcloudshare permalink-get <permalink-id>` | Get permalink details |

## Teams

| Command | Description |
|---------|-------------|
| `mxcloudshare team-list` | List all teams |
| `mxcloudshare team-create <name>` | Create a team |

## Invitations

| Command | Description |
|---------|-------------|
| `mxcloudshare invite-project-member <email> <project-id> <role>` | Invite someone to a project (roles: Owner, Editor, Viewer) |
| `mxcloudshare invite-to-poc <email> <topology-id>` | Invite someone to a proof-of-concept |
| `mxcloudshare login-url` | Get a login URL for the current user |

## Environment creation

```bash
mxcloudshare env-create <blueprint-id> [--policy-id <id>] [--name MyEnv] [--count 3]
```

Creates one or more environments from a blueprint. When `--count` is greater than 1, names are suffixed with `-1`, `-2`, etc.

## Shared environments and public cloud

```bash
mxcloudshare shared-env-get <project-id> <blueprint-id> <region-id> <class-id>
mxcloudshare public-cloud-get <environment-id>
```

Gets shared environment information and public cloud (external cloud provider) details for an environment.

## Utility commands

```bash
mxcloudshare ping                        # Test API connectivity
mxcloudshare region-list                 # List all regions
mxcloudshare timezone-list               # List all timezones
```

## The generic API escape hatch

The `api-call` command lets you reach **any** CloudShare REST API v3 endpoint, even ones without a typed wrapper:

```bash
mxcloudshare api-call GET /envs --query limit=20
mxcloudshare api-call POST /envs/actions/create --body '{"blueprintId":"...","name":"demo"}'
mxcloudshare api-call PUT /envs/actions/suspend --query envId=EN123
mxcloudshare api-call DELETE /envs/EN123
```

Supports GET, POST, PUT, DELETE, PATCH, and OPTIONS methods. Query parameters use `--query key=value` (repeatable). The body is a JSON string with `--body`.

## Output formats

All data-returning commands accept `--outformat <format>`:

| Format | Description |
|--------|-------------|
| `json` (default) | Pretty-printed JSON via Rich |
| `table` | Formatted table with sorted column names |
| `card` | Key-value pairs (single item) or table (multiple items) |
| `csv` | CSV output with all fields quoted |

Example:

```bash
mxcloudshare env-show-all --outformat table --tablewidth 120
```

## Troubleshooting

- **"CLOUDSHARE_API_ID and CLOUDSHARE_API_KEY not found"** — Create a `cloudshare.env` file, export the environment variables, or use `--keyfile`.
- **Non-2xx API response** — The tool prints the HTTP status and error message from the API and exits. Check the endpoint path and parameters.
- **Operation times out** — The poll loop (6-second intervals, 20 retries = 2 minutes max) may not be long enough for slow environments. This is a log message, not a hard failure — the operation may still complete on the server.
- **Debugging** — Use `--loglevel DEBUG --logfile debug.log` to capture full request details and API responses.
- **"No environments found"** — Confirm your API credentials have access to the target CloudShare account and that environments exist.