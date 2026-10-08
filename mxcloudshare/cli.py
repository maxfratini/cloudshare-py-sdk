import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from cyclopts import App, Parameter
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.table import Table

from mxcloudshare import mxcloudshare as cs
from mxcloudshare.mxutils import mxLogging

mxlogger = mxLogging.getLogger(__name__)

# ##############
# Global objects
#
try:
    from importlib.metadata import version as _pkg_version
    _VERSION = _pkg_version("mxcloudshare")
except Exception:
    _VERSION = "0.0.0"

cs_app = App(name="mxCloudShare", help="Cloudshare automation tool", version=_VERSION)


class OutFormat(str, Enum):
    csv_fmt = "csv"
    json_fmt = "json"
    table_fmt = "table"
    card_fmt = "card"


class EnvStatus(str, Enum):
    ready = "Ready"
    suspended = "Suspended"
    archived = "Archived"
    deleted = "Deleted"
    taking_snapshot = "Taking a Snapshot"
    preparing = "Preparing"
    creation_failed = "Creation Failed"


@dataclass
class AppConfig:
    """Application configuration. Replaces the globalconf mutable dict."""
    outputformat: str = OutFormat.json_fmt
    tablewidth: int = 80
    api_id: str = None
    api_key: str = None


@Parameter(name="*")  # Flatten the namespace; i.e. option will be "--url" instead of "--common.url"
@dataclass
class mxCommonOpts:
    # sfrutta le annotazioni di tipo (type hints) e docstring su singola riga in un formato particolare supportato da Cyclopts.
    outformat: str = OutFormat.json_fmt
    "Set output format."

    tablewidth: int = 80
    "Set table output width."

    keyfile: Annotated[str, Parameter(name=["--keyfile", "-k"])] = None
    "Path to CloudShare authentication keys file."

    loglevel: str = "PRINT"
    "Set the logging level"

    logfile: str | None = None
    "Path to save the log file."


#
# END Global objects
# ################


# Initialize the application and return a config object (no global state)
def initializeApp(commopts: mxCommonOpts | None) -> AppConfig:

    # cyclopts leaves the dataclass as None when none of its options were given
    # on the command line, so fall back to the declared defaults.
    if commopts is None:
        commopts = mxCommonOpts()

    mxlogger.setup_mxLogger(log_file=commopts.logfile, log_level=commopts.loglevel)
    if commopts.loglevel.upper() in ["INFO", "DEBUG"]:
        mxlogger.info("LogLevel is set to %s", logging.getLevelName(logging.getLogger().getEffectiveLevel()))

    # Load auth keys
    _API_ID, _API_KEY = loadKeys(commopts.keyfile)
    mxlogger.debug(f"Loaded API_ID: {_API_ID} and API_KEY: {_API_KEY}")

    config = AppConfig(
        outputformat=commopts.outformat,
        tablewidth=commopts.tablewidth,
        api_id=_API_ID,
        api_key=_API_KEY,
    )

    cs.cs_set_auth_keys(_API_ID, _API_KEY)

    return config


def get_timestamp():
    return str(int(time.time()))


# ################################################################################
def _flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dict into a single-level dict.
    
    Args:
        d: Dictionary to flatten
        parent_key: Key prefix for nested keys
        sep: Separator between parent and child keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, str(v) if v is not None else ''))
    return dict(items)


def _dict_to_rows(data):
    """Convert data (list of dicts or single dict) into flattened rows.
    
    Args:
        data: List of dicts or single dict to convert
    
    Returns:
        Tuple of (rows, column_names) where rows is list of lists and column_names is list of strings
    """
    if isinstance(data, dict):
        data = [data]
    
    # Flatten all dicts and collect all unique keys
    flattened_data = [_flatten_dict(item) if isinstance(item, dict) else {} for item in data]
    all_keys = set()
    for flat_dict in flattened_data:
        all_keys.update(flat_dict.keys())
    
    # Sort keys for consistent column order
    column_names = sorted(all_keys)
    
    # Create rows
    rows = []
    for flat_dict in flattened_data:
        row = [str(flat_dict.get(key, '')) for key in column_names]
        rows.append(row)
    
    return rows, column_names


def _filter_fields(data, field, availfields):
    """Filter data to show only specified fields, or show available fields and exit.
    
    Args:
        data: List of dicts to filter
        field: List of field names to keep (empty list = keep all)
        availfields: If True, print available keys and exit
    
    Returns:
        Filtered list of dicts (in-place modification of input)
    """
    if availfields:
        all_keys = set().union(*(d.keys() for d in data))
        mxlogger.info(all_keys)
        sys.exit()

    if field:
        for item in data:
            unwanted = set(item) - set(field)
            for unwanted_key in unwanted:
                del item[unwanted_key]

    return data


def _parse_json_input(json_input: str) -> dict:
    """Parse a JSON string or @-referenced JSON file.

    Args:
        json_input: Raw JSON string or ``@filepath`` pointing to a JSON file.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If the JSON is malformed.
    """
    if json_input.startswith("@"):
        filepath = json_input[1:]
        with open(filepath) as f:
            return json.load(f)
    return json.loads(json_input)


def print_as_table(d, config: AppConfig = None):
    """Print data as a formatted table
    
    Args:
        d: Data to display (list or dict)
        config: Application configuration
    """
    # Provide default config if not given
    if config is None:
        config = AppConfig()
    
    # Initiate a Table instance to be modified
    table = Table(show_header=True, header_style="bold")
    
    # Convert data to rows without pandas
    if isinstance(d, dict):
        d = [d]
    
    rows, column_names = _dict_to_rows(d)
    
    # Modify the table instance to have the data
    for col in column_names:
        table.add_column(col)
    
    for row in rows:
        table.add_row(*row)
    
    # Update the style of the table
    table.row_styles = ["none", "dim"]
    table.box = box.SIMPLE_HEAD
    console = Console(width=config.tablewidth)
    console.print(table)


def print_results(data, config: AppConfig = None):
    """Display results with support for multiple output formats
    
    Args:
        data: Data to display (list or dict)
        config: Application configuration (holds outputformat setting)
    """
    # Provide default config if not given
    if config is None:
        config = AppConfig()
    
    if isinstance(data, dict):
        data = [data]
    
    # Get output format from config
    outputformat = config.outputformat
    
    if outputformat == OutFormat.csv_fmt:
        # CSV output using stdlib csv for proper quoting
        import csv
        import io
        rows, column_names = _dict_to_rows(data)
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(column_names)
        for row in rows:
            writer.writerow(row)
        console = Console(width=config.tablewidth)
        console.print(output.getvalue())
    elif outputformat == OutFormat.json_fmt:
        # JSON output
        import json
        out = json.dumps(data, indent=2)
        console = Console(width=config.tablewidth)
        console.print_json(out)
    elif outputformat == OutFormat.card_fmt:
        # Card format - simple key-value pairs
        if len(data) == 1:
            item = data[0]
            console = Console(width=config.tablewidth)
            for key, value in item.items():
                console.print(f"[bold]{key}[/bold]: {value}")
        else:
            # Table format for multiple items
            print_results(data, config)  # Recurse with table format
    else:
        # Default to table format (including "table" and any unrecognized format)
        show_results(data, config=config)


def show_results(data, title=None, config: AppConfig = None):
    """Display results in a formatted table
    
    Args:
        data: Data to display (list or dict)
        title: Optional title for the table
        config: Application configuration
    """
    # Provide default config if not given
    if config is None:
        config = AppConfig()
    
    console = Console(width=config.tablewidth)

    if isinstance(data, dict):
        data = [data]

    # Convert data to rows without pandas
    rows, column_names = _dict_to_rows(data)
    
    table = Table(show_header=True, header_style="bold", title=title)
    
    # Add columns
    for col in column_names:
        table.add_column(col)
    
    # Add rows
    for row in rows:
        table.add_row(*row)
    
    table.row_styles = ["none", "dim"]
    table.box = box.SIMPLE_HEAD
    
    console.print(table)
    
    return len(data)


@cs_app.command()
def env_show_all(
    common: mxCommonOpts | None = None,
):
    """
    Show all environments
    """
    config = initializeApp(common)

    mxlogger.print("Getting all environments...")
    envs = cs.cs_get("envs/?brief=false")
    mxlogger.print("...done")
    mxlogger.debug(f"envs: {envs}")

    if len(envs) == 0:
        mxlogger.print("No environments found")

    i = 0
    brief_envs = []
    for e in envs:
        i += 1
        brief_env = {}
        brief_env["index"] = i
        brief_env["id"] = e.get("id", "")
        brief_env["name"] = e.get("name", "")
        brief_env["status"] = e.get("status", "")
        brief_env["owner"] = e.get("ownerEmail", "")
        brief_envs.append(brief_env)

    print_results(brief_envs, config)


def env_wait_condition(envId: str, checks: str, delay_secs: int = 3, max_retry: int = 10, operation: str | None = None):
    """
    Poll an environment for a status

    Args:
        envId: environment id
        checks: list of dicts with conditions to check for. dict should contain:
            - property: property of vms to check for
            - check_fn: function to execute against property that must be true
        delay_secs: seconds to wait between polls
        max_retry: maximum number of retries
        operation: optional label shown in Rich progress bar (e.g. "Suspending env-abc123").
                   When None, no progress bar is shown (original behavior).
    """
    from rich.console import Console as RichConsole
    from rich.progress import Progress, TextColumn, TimeElapsedColumn

    stillWorking = True
    retries = 0

    _progress = None
    _task_id = None
    if operation is not None:
        _progress = Progress(
            TextColumn("{task.description}"),
            TimeElapsedColumn(),
            transient=True,
            console=RichConsole(stderr=True),
        )
        _progress.start()
        _task_id = _progress.add_task(operation, total=max_retry)

    try:
        while stillWorking and retries < max_retry:
            machines = cs.get_vms(envId)
            retries += 1
            for m in machines:
                stillWorking = False
                # check if all conditions are met
                for condition in checks:
                    property_name = condition["property"]
                    check_fn = condition["check_fn"]
                    if property_name not in m:
                        raise Exception(f"VM {m['name']} does not have property {property_name}")

                    if not check_fn(m[property_name]):
                        mxlogger.debug(f"VM {m['name']} failed condition: {property_name} is {m[property_name]}, let's wait more...")
                        mxlogger.debug(f"VM is {json.dumps(m, indent=2, sort_keys=True)}")
                        stillWorking = True
                        if _progress is not None:
                            status_val = m.get(property_name, "unknown")
                            _progress.update(
                                _task_id,
                                description=f"[cyan]{retries}/{max_retry}[/] {operation} — {property_name}: {status_val}",
                                advance=1,
                            )
                        # stop checking at first condition failed and wait next retry
                        break
                # stop checking as soon as a VM failed, and wait next retry
                if stillWorking:
                    break

            # if still working, wait for delay_secs before next retry
            if stillWorking:
                mxlogger.info(f"Polling status #{retries}, waiting {delay_secs} seconds...")
                if _progress is not None:
                    _progress.update(
                        _task_id,
                        description=f"[cyan]{retries}/{max_retry}[/] {operation} — retrying in {delay_secs}s...",
                        advance=1,
                    )
                time.sleep(delay_secs)

        # When we get here, either job completed (stillWorking=False) or we timed out (stillWorking=True)
        if stillWorking:
            mxlogger.debug("Timed out waiting for environment to reach desired state")
            if _progress is not None:
                _progress.update(_task_id, description=f"[red]Timed out[/] — {operation}")
            return False
        else:
            mxlogger.debug("Environment reached desired state")
            if _progress is not None:
                _progress.update(_task_id, description=f"[green]Ready[/] — {operation}")
            return True
    finally:
        if _progress is not None:
            _progress.stop()


#
@cs_app.command()
def env_suspend(
    envId_list: Annotated[list[str], Parameter(name=["--envId", "-e"], negative=False)],
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Suspend an environment

    Args:
        envId_list (List[str]): Environment Id, specify multiple time for list of ids.
    """

    initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Suspended"}]

    for envId in envId_list:
        mxlogger.info(f"Suspending environment {envId}")
        if dry_run:
            mxlogger.info(f"[DRY-RUN] Would suspend environment {envId}")
            continue
        # Check if the environment is in a state that can be suspended
        status = cs.env_get_status(envId)
        if status != EnvStatus.ready:
            mxlogger.info(f"Environment {envId} is not in a state that can be suspended (current status: {status})")
            continue
        # Suspend the environment
        cs.cs_env_suspend(envId)

        mxlogger.info("Suspend Started")
        # Wait for the environment to reach the desired state
        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20, operation=f"Suspending {envId}")
        if completed:
            mxlogger.info(f"Suspend of environment {envId} completed!")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Suspended state")


#
@cs_app.command()
def env_delete(
    envId_list: Annotated[list[str], Parameter(name=["--envid", "-e"], negative=False)],
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Delete an environment
    Args:
        envId_list (Annotated[List[str], required): Environment Id, repeat multiple time for list of ids.
    """
    initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Deleted"}]

    for envId in envId_list:
        mxlogger.info(f"Deleting environment {envId}")
        if dry_run:
            mxlogger.info(f"[DRY-RUN] Would delete environment {envId}")
            continue
        # Check if the environment is in a state that can be deleted
        status = cs.env_get_status(envId)
        if status == EnvStatus.deleted:
            mxlogger.info(f"Environment {envId} is not in a state that can be deleted (current status: {status})")
            continue
        # Delete the environment
        cs.cs_env_delete(envId)
        mxlogger.info("Delete Started!")
        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20, operation=f"Deleting {envId}")
        if completed:
            mxlogger.info(f"Delete of environment {envId} completed!")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Deleted state")


#
@cs_app.command()
def env_resume(
    envId_list: Annotated[list[str], Parameter(name=["--envid", "-e"], negative=False)],
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Resume a paused environment
    Args:
        envId_list (Annotated[List[str], required): Environment Id, repeat multiple time for list of ids.
    """
    initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Running"}]

    for envId in envId_list:
        mxlogger.info(f"Resuming environment {envId}")
        if dry_run:
            mxlogger.info(f"[DRY-RUN] Would resume environment {envId}")
            continue
        # Check if the environment is in a state that can be resumed
        status = cs.env_get_status(envId)
        if status != EnvStatus.suspended:
            mxlogger.info(f"Environment {envId} is not in a state that can be resumed (current status: {status})")
            continue
        # Resume the environment
        cs.cs_env_resume(envId)
        mxlogger.info("Resume Started")

        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20, operation=f"Resuming {envId}")
        if completed:
            mxlogger.info(f"Resume completed for environment {envId}")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Resumed state")


@cs_app.command()
def env_get_vms_info(
    envid: Annotated[str, Parameter(help="Environment Id")],
    field: Annotated[list[str] | None, Parameter(name=["--field", "-f"], negative=False)] = [],
    availfields: Annotated[bool | None, Parameter(name=["--all", "-a"], negative=False)] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """Show all VMs info for an environment
    Args:
        envid (Annotated[str], required): Environment Id
        field (Annotated[Optional[List[str]]], optional): Attribute to show (repeat for multiple attributes). Defaults to [].
        availfields (Annotated[Optional[bool]], optional): Show all available attributes. Defaults to False.
    """
    config = initializeApp(common)

    machines = cs.get_vms(envid)
    _filter_fields(machines, field, availfields)

    print_results(machines, config)


@cs_app.command()
def env_get_info(
    envid: Annotated[str, Parameter(help="Environment Id")],
    field: Annotated[list[str] | None, Parameter(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[bool | None, Parameter(help="Show all available attributes")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Show info for an environment
    """
    config = initializeApp(common)

    e = cs.cs_env_get(envid)
    _filter_fields(e, field, availfields)

    print_results(e, config)


@cs_app.command()
def blueprint_list(
    project_id: Annotated[str | None, Parameter(name=["--project-id"], help="Project ID for project-scoped blueprints")] = None,
    field: Annotated[list[str] | None, Parameter(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[bool | None, Parameter(help="Show all available attributes")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Show all available blueprints
    """

    config = initializeApp(common)

    if project_id:
        blueprints = cs.cs_project_blueprints_get_all(project_id)
    else:
        blueprints = cs.cs_blueprint_get_all()

    _filter_fields(blueprints, field, availfields)

    print_results(blueprints, config)


@cs_app.command()
def policy_list(
    project_id: Annotated[str | None, Parameter(name=["--project-id"], help="Project ID for project-scoped policies")] = None,
    field: Annotated[list[str] | None, Parameter(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[bool | None, Parameter(help="Show all available attributes")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Show all available policies
    """
    config = initializeApp(common)

    if project_id:
        policies = cs.cs_project_policies_get_all(project_id)
    else:
        policies = cs.cs_policy_get_all()

    _filter_fields(policies, field, availfields)

    print_results(policies, config)


@cs_app.command()
def env_create(
    blueprint_id: Annotated[str, Parameter(help="Blueprint ID to create environment from")],
    policy_id: Annotated[str, Parameter(help="Policy ID to use")] = None,
    name: Annotated[str, Parameter(help="Name for the new environment")] = None,
    description: Annotated[str, Parameter(help="Description for the new environment")] = None,
    count: Annotated[int, Parameter(help="Number of environments to create")] = 1,
    *,
    json_input: Annotated[str | None, Parameter(name=["--json"], help='JSON string or @file.json path with creation params (merged over individual params)')] = None,
    common: mxCommonOpts | None = None,
):
    """
    Create one or more environments from a blueprint
    """
    config = initializeApp(common)

    # Merge --json overrides into individual params
    if json_input is not None:
        try:
            overrides = _parse_json_input(json_input)
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Invalid --json input: {exc}") from exc
        blueprint_id = overrides.get("blueprintId", blueprint_id)
        policy_id = overrides.get("policyId", policy_id)
        name = overrides.get("name", name)
        description = overrides.get("description", description)
        count = overrides.get("count", count)

    results = []
    for i in range(count):
        result = cs.cs_env_create(blueprint_id, policy_id, f"{name}-{i+1}", description)
        results.append(result)

    print_results(results, config)


@cs_app.command()
def class_create(
    blueprint_id: Annotated[str, Parameter(help="Blueprint ID to create class from")],
    policy_id: Annotated[str, Parameter(help="Policy ID to use")] = None,
    name: Annotated[str, Parameter(help="Base name for the new classes")] = None,
    description: Annotated[str, Parameter(help="Description for the new classes")] = None,
    count: Annotated[int, Parameter(help="Number of classes to create")] = 1,
    *,
    json_input: Annotated[str | None, Parameter(name=["--json"], help='JSON string or @file.json path with creation params (merged over individual params)')] = None,
    common: mxCommonOpts | None = None,
):
    """
    Create one or more classes with numbered suffixes
    """
    config = initializeApp(common)

    # Merge --json overrides into individual params
    if json_input is not None:
        try:
            overrides = _parse_json_input(json_input)
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Invalid --json input: {exc}") from exc
        blueprint_id = overrides.get("blueprintId", blueprint_id)
        policy_id = overrides.get("policyId", policy_id)
        name = overrides.get("name", name)
        description = overrides.get("description", description)
        count = overrides.get("count", count)

    mxlogger.info(f"Creating {count} classes")
    results = []
    for i in range(count):
        mxlogger.info(f"Creating class {i+1}")
        result = cs.cs_class_create(blueprint_id, policy_id, f"{name}-{i+1}", description)
        results.append(result)

    print_results(results, config)


@cs_app.command()
def class_clone(
    class_id: Annotated[str, Parameter(help="Class ID to clone from")],
    count: Annotated[int, Parameter(help="Number of clones to create")] = 1,
    name_suffix: Annotated[str, Parameter(help="Base suffix for the cloned classes")] = "",
    *,
    common: mxCommonOpts | None = None,
):
    """
    Clone an existing class multiple times with numbered suffixes
    """
    config = initializeApp(common)

    mxlogger.info(f"Cloning class {class_id} {count} times")

    # Get original class details
    original_class = cs.cs_class_get(class_id)
    results = []

    for i in range(count):
        mxlogger.info(f"Creating clone {i+1}")
        result = cs.cs_class_create(
            original_class["blueprintId"],
            original_class["policyId"],
            f"{original_class['name']}{name_suffix}{i+1}",
            original_class["description"],
        )
        results.append(result)

    print_results(results, config)


@cs_app.command()
def class_setstatus(
    class_pattern: Annotated[str, Parameter(help="Regex pattern to match class name")],
    status: Annotated[str, Parameter(help="Set status of the class ACTIVE|SUSPENDED")] = "ACTIVE",
    by_id: Annotated[bool, Parameter(help="Match pattern against class IDs instead of names")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Suspend or resume classes matching the specified regex pattern
    """
    config = initializeApp(common)

    import re

    status = status.upper()
    action = "resuming" if status == "ACTIVE" else "suspending"
    mxlogger.info(f"{action.capitalize()} classes matching pattern: {class_pattern}")

    # Get all classes
    classes = cs.cs_class_get_all()
    pattern = re.compile(class_pattern)

    results = []
    for class_item in classes:
        match_field = class_item["id"] if by_id else class_item["name"]
        if pattern.search(match_field):
            mxlogger.info(f"{action.capitalize()} class {class_item['id']} ({class_item['name']})")
            payload = {"status": "active" if status else "suspended"}
            result = cs.cs_class_update(class_item["id"], payload)

            results.append(result)

    if not results:
        mxlogger.info("No classes found matching the pattern")
        return

    print_results(results, config)


@cs_app.command()
def class_show_all(
    *,
    common: mxCommonOpts | None = None,
):
    config = initializeApp(common)

    classes = cs.cs_class_get_all()

    if len(classes) == 0:
        mxlogger.info("No classes found")
    # i = 0
    # for c in classes:
    #     i += 1
    #     c["status"] = cs.env_get_status(c.get("id", ""))
    #     c["index"] = i

    print_results(classes, config)


@cs_app.command()
def class_get(
    class_id,
    *,
    common: mxCommonOpts | None = None,
):
    initializeApp(common)

    clas = cs.cs_class_get(class_id)
    mxlogger.info("class name: {0}".format(clas["name"]))


@cs_app.command()
def class_delete(
    class_pattern: Annotated[str, Parameter(help="Regex pattern to match class name or ID")],
    by_id: Annotated[bool, Parameter(help="Match pattern against class IDs instead of names")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Delete classes matching the specified regex pattern (matches against names by default)
    """
    config = initializeApp(common)

    import re

    mxlogger.info(f"Deleting classes matching pattern: {class_pattern}")

    # Get all classes
    classes = cs.cs_class_get_all()
    pattern = re.compile(class_pattern)

    results = []
    for class_item in classes:
        match_field = class_item["id"] if by_id else class_item["name"]
        if pattern.search(match_field):
            if class_item.get("status") != "deleted":
                mxlogger.info(f"Deleting class {class_item['id']} ({class_item['name']})")
                cs.cs_class_delete(class_item["id"])
                results.append({"id": class_item["id"], "name": class_item["name"], "status": "deleted"})
            else:
                mxlogger.info(f"Skipping class {class_item['id']} ({class_item['name']}) - already deleted")
    if not results:
        mxlogger.info("No classes found matching the pattern")
        return

    print_results(results, config)


@cs_app.command()
def class_list(
    fields: Annotated[str, Parameter(help="Comma-separated list of fields to display")] = "id,name",
    pattern: Annotated[str, Parameter(help="Regex pattern to match class names")] = ".*",
    *,
    common: mxCommonOpts | None = None,
):
    """
    List all classes with specified fields (defaults to id and name)
    """

    config = initializeApp(common)

    import re

    mxlogger.info("Listing classes")
    results = cs.cs_class_get_all()
    pattern = re.compile(pattern)
    filtered_results = []
    field_list = fields.split(",")

    for item in results:
        if pattern.search(item["name"]):
            item_filtered_fields = {field: item[field] for field in field_list if field in item}
            filtered_results.append(item_filtered_fields)
    print_results(filtered_results, config)


# ──────────────────────────────────────────
# Environment lifecycle commands
# ──────────────────────────────────────────


@cs_app.command()
def env_extend(
    envId_list: Annotated[list[str], Parameter(name=["--envId", "-e"], negative=False)],
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Extend an environment's duration"""
    initializeApp(common)
    for envId in envId_list:
        mxlogger.info(f"Extending environment {envId}")
        if dry_run:
            mxlogger.info(f"[DRY-RUN] Would extend environment {envId}")
            continue
        cs.cs_env_extend(envId)
        mxlogger.info(f"Environment {envId} extended")


@cs_app.command()
def env_revert(
    envId_list: Annotated[list[str], Parameter(name=["--envId", "-e"], negative=False)],
    snapshot_id: Annotated[str | None, Parameter(name=["--snapshot-id"], help="Snapshot ID to revert to")] = None,
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Revert an environment to a snapshot (polls until Ready)"""
    initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Ready"}]

    for envId in envId_list:
        mxlogger.info(f"Reverting environment {envId}")
        if dry_run:
            mxlogger.info(f"[DRY-RUN] Would revert environment {envId}")
            continue
        cs.cs_env_revert(envId, snapshot_id)
        mxlogger.info("Revert Started")

        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20, operation=f"Reverting {envId}")
        if completed:
            mxlogger.info(f"Revert of environment {envId} completed!")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Ready state")


@cs_app.command()
def env_postpone(
    envId_list: Annotated[list[str], Parameter(name=["--envId", "-e"], negative=False)],
    *,
    common: mxCommonOpts | None = None,
):
    """Postpone inactivity timeout for an environment"""
    initializeApp(common)
    for envId in envId_list:
        mxlogger.info(f"Postponing inactivity for environment {envId}")
        cs.cs_env_postpone_inactivity(envId)
        mxlogger.info(f"Inactivity postponed for environment {envId}")


# ──────────────────────────────────────────
# Snapshot commands
# ──────────────────────────────────────────


@cs_app.command()
def snapshot_take(
    envId: Annotated[str, Parameter(help="Environment Id")],
    name: Annotated[str, Parameter(help="Snapshot name")],
    set_as_default: Annotated[bool | None, Parameter(name=["--set-as-default"], help="Set as default snapshot")] = None,
    description: Annotated[str | None, Parameter(help="Snapshot description")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Take a snapshot of an environment"""
    config = initializeApp(common)
    result = cs.cs_snapshot_take(envId, name, set_as_default=set_as_default, description=description)
    print_results(result, config)


@cs_app.command()
def snapshot_list(
    envid: Annotated[str, Parameter(help="Environment Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """List snapshots for an environment"""
    config = initializeApp(common)
    snapshots = cs.cs_snapshot_get_for_env(envid)
    print_results(snapshots, config)


@cs_app.command()
def snapshot_mark_default(
    snapshot_id: Annotated[str, Parameter(help="Snapshot Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Mark a snapshot as the default for its blueprint"""
    config = initializeApp(common)
    result = cs.cs_snapshot_mark_default(snapshot_id)
    print_results(result, config)


# ──────────────────────────────────────────
# VM commands
# ──────────────────────────────────────────


@cs_app.command()
def vm_reboot(
    vmId_list: Annotated[list[str], Parameter(name=["--vmId", "-v"], negative=False)],
    *,
    common: mxCommonOpts | None = None,
):
    """Reboot a VM"""
    initializeApp(common)
    for vmId in vmId_list:
        mxlogger.info(f"Rebooting VM {vmId}")
        cs.cs_vm_reboot(vmId)
        mxlogger.info(f"VM {vmId} rebooted")


@cs_app.command()
def vm_revert(
    vmId_list: Annotated[list[str], Parameter(name=["--vmId", "-v"], negative=False)],
    snapshot_id: Annotated[str | None, Parameter(name=["--snapshot-id"], help="Snapshot ID to revert to")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Revert a VM to a snapshot"""
    initializeApp(common)
    for vmId in vmId_list:
        mxlogger.info(f"Reverting VM {vmId}")
        cs.cs_vm_revert(vmId, snapshot_id)
        mxlogger.info(f"VM {vmId} reverted")


@cs_app.command()
def vm_delete(
    vmId_list: Annotated[list[str], Parameter(name=["--vmId", "-v"], negative=False)],
    *,
    common: mxCommonOpts | None = None,
):
    """Delete a VM"""
    initializeApp(common)
    for vmId in vmId_list:
        mxlogger.info(f"Deleting VM {vmId}")
        cs.cs_vm_delete(vmId)
        mxlogger.info(f"VM {vmId} deleted")


@cs_app.command()
def vm_hardware(
    vmId: Annotated[str, Parameter(help="VM Id")],
    payload: Annotated[str, Parameter(help='JSON string with hardware settings (e.g. \'{"numCpus":4,"memorySizeMBs":8192}\')')],
    *,
    common: mxCommonOpts | None = None,
):
    """Edit VM hardware (numCpus, memorySizeMBs, diskSizeGBs)"""
    config = initializeApp(common)
    payload_dict = json.loads(payload)
    result = cs.cs_vm_edit_hardware(vmId, payload_dict)
    print_results(result, config)


@cs_app.command()
def vm_remote_access(
    vmId: Annotated[str, Parameter(help="VM Id")],
    desktop_width: Annotated[int | None, Parameter(name=["--desktop-width"], help="Desktop width in pixels")] = None,
    desktop_height: Annotated[int | None, Parameter(name=["--desktop-height"], help="Desktop height in pixels")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Get remote access file for a VM"""
    config = initializeApp(common)
    result = cs.cs_vm_get_remote_access_file(vmId, desktop_width=desktop_width, desktop_height=desktop_height)
    print_results(result, config)


# ──────────────────────────────────────────
# Generic API call escape hatch
# ──────────────────────────────────────────


@cs_app.command()
def api_call(
    method: Annotated[str, Parameter(help="HTTP method (GET, POST, PUT, DELETE, PATCH, OPTIONS)")],
    path: Annotated[str, Parameter(help="API path (e.g. /envs)")],
    query: Annotated[list[str] | None, Parameter(name=["--query"], negative=False, help="Query parameter in k=v form (repeatable)")] = None,
    body: Annotated[str | None, Parameter(help="JSON body string")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Make a generic API call to any CloudShare endpoint"""
    config = initializeApp(common)

    query_params = None
    if query:
        query_params = {}
        for q in query:
            k, _, v = q.partition("=")
            query_params[k] = v

    payload = json.loads(body) if body else None
    result = cs.cs_api_call(method.upper(), path, payload=payload, queryParams=query_params)
    print_results(result, config)


# ──────────────────────────────────────────
# Class action commands
# ──────────────────────────────────────────


@cs_app.command()
def class_sendinvitations(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_ids: Annotated[list[str], Parameter(name=["--student-id"], negative=False, help="Student ID (repeatable)")],
    is_multiple: Annotated[bool | None, Parameter(name=["--is-multiple"], help="Send as multiple invitations")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Send invitations to students in a class"""
    initializeApp(common)
    mxlogger.info(f"Sending invitations to class {class_id}")
    cs.cs_class_send_invitations(
        class_id, student_ids,
        is_multiple=is_multiple if is_multiple is not None else True,
    )
    mxlogger.info("Invitations sent")


@cs_app.command()
def class_suspend_all(
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Suspend all environments in a class"""
    initializeApp(common)
    mxlogger.info(f"Suspending all environments in class {class_id}")
    cs.cs_class_suspend_all_environments(class_id)
    mxlogger.info("All environments suspended")


@cs_app.command()
def class_delete_all(
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"], help="Print what would be done without executing")] = False,
    common: mxCommonOpts | None = None,
):
    """Delete all environments in a class"""
    initializeApp(common)
    mxlogger.info(f"Deleting all environments in class {class_id}")
    if dry_run:
        mxlogger.info(f"[DRY-RUN] Would delete all environments in class {class_id}")
        return
    cs.cs_class_delete_all_environments(class_id)
    mxlogger.info("All environments deleted")


@cs_app.command()
def class_sponsoredlink(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_email: Annotated[str, Parameter(help="Student email")],
    action: Annotated[str, Parameter(name=["--action"], help="Action: 'create' or 'disable'")] = "create",
    first_name: Annotated[str | None, Parameter(name=["--first-name"], help="Student first name (create only)")] = None,
    last_name: Annotated[str | None, Parameter(name=["--last-name"], help="Student last name (create only)")] = None,
    pre_register: Annotated[bool | None, Parameter(name=["--pre-register"], help="Pre-register student (create only)")] = None,
    unregister_student: Annotated[bool | None, Parameter(name=["--unregister-student"], help="Unregister student when disabling")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Create or disable a sponsored link for a student"""
    config = initializeApp(common)
    if action == "create":
        mxlogger.info(f"Creating sponsored link for {student_email} in class {class_id}")
        result = cs.cs_class_create_sponsored_link(
            class_id, student_email,
            student_first_name=first_name,
            student_last_name=last_name,
            pre_register=pre_register if pre_register is not None else False,
        )
    elif action == "disable":
        mxlogger.info(f"Disabling sponsored link for {student_email} in class {class_id}")
        result = cs.cs_class_disable_sponsored_link(
            class_id, student_email,
            unregister_student=unregister_student if unregister_student is not None else False,
        )
    else:
        raise ValueError(f"Unsupported action: {action}")
    print_results(result, config)


@cs_app.command()
def class_detailed(
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get detailed class information"""
    config = initializeApp(common)
    result = cs.cs_class_get_detailed(class_id)
    print_results(result, config)


@cs_app.command()
def class_countries(
    *,
    common: mxCommonOpts | None = None,
):
    """Get list of countries for class registration"""
    config = initializeApp(common)
    result = cs.cs_class_get_countries()
    print_results(result, config)


@cs_app.command()
def class_custom_fields(
    *,
    common: mxCommonOpts | None = None,
):
    """Get custom fields for class registration"""
    config = initializeApp(common)
    result = cs.cs_class_get_custom_fields()
    print_results(result, config)


@cs_app.command()
def class_resume_student(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_ids: Annotated[list[str], Parameter(name=["--student-id"], negative=False, help="Student ID (repeatable)")],
    *,
    common: mxCommonOpts | None = None,
):
    """Resume environment for a student in a class"""
    initializeApp(common)
    mxlogger.info(f"Resuming environment for students in class {class_id}")
    cs.cs_class_resume_student_environment(class_id, student_ids)
    mxlogger.info("Environment resumed")


# ──────────────────────────────────────────
# Student CRUD commands
# ──────────────────────────────────────────


@cs_app.command()
def student_list(
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """List all students in a class"""
    config = initializeApp(common)
    students = cs.cs_class_student_get_all(class_id)
    print_results(students, config)


@cs_app.command()
def student_get(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_id: Annotated[str, Parameter(help="Student Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get a specific student by ID"""
    config = initializeApp(common)
    student = cs.cs_class_student_get(class_id, student_id)
    print_results(student, config)


@cs_app.command()
def student_create(
    class_id: Annotated[str, Parameter(help="Class Id")],
    email: Annotated[str, Parameter(help="Student email")],
    first_name: Annotated[str | None, Parameter(name=["--first-name"], help="Student first name")] = None,
    last_name: Annotated[str | None, Parameter(name=["--last-name"], help="Student last name")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Create a student in a class"""
    config = initializeApp(common)
    mxlogger.info(f"Creating student {email} in class {class_id}")
    result = cs.cs_class_student_create(class_id, email, first_name=first_name, last_name=last_name)
    print_results(result, config)


@cs_app.command()
def student_update(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_id: Annotated[str, Parameter(help="Student Id")],
    payload: Annotated[str, Parameter(help='JSON payload string (e.g. \'{"email":"new@example.com"}\')')],
    *,
    common: mxCommonOpts | None = None,
):
    """Update a student in a class"""
    config = initializeApp(common)
    payload_dict = json.loads(payload)
    mxlogger.info(f"Updating student {student_id} in class {class_id}")
    result = cs.cs_class_student_update(class_id, student_id, payload_dict)
    print_results(result, config)


@cs_app.command()
def student_delete(
    class_id: Annotated[str, Parameter(help="Class Id")],
    student_id: Annotated[str, Parameter(help="Student Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Delete a student from a class"""
    initializeApp(common)
    mxlogger.info(f"Deleting student {student_id} from class {class_id}")
    cs.cs_class_student_delete(class_id, student_id)
    mxlogger.info("Student deleted")


# ──────────────────────────────────────────
# Instructor CRUD commands
# ──────────────────────────────────────────


@cs_app.command()
def instructor_list(
    class_id: Annotated[str | None, Parameter(name=["--class-id"], help="Filter by class Id")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """List instructors, optionally filtered by class"""
    config = initializeApp(common)
    instructors = cs.cs_instructor_get_by_class(class_id)
    print_results(instructors, config)


@cs_app.command()
def instructor_create(
    instructor_vup_id: Annotated[str, Parameter(help="Instructor VUP Id")],
    class_id: Annotated[str, Parameter(help="Class Id")],
    send_invite_now: Annotated[bool | None, Parameter(name=["--send-invite-now"], help="Send invitation now")] = None,
    disable_env_creation: Annotated[bool | None, Parameter(name=["--disable-env-creation"], help="Disable environment creation for instructor")] = None,
    *,
    common: mxCommonOpts | None = None,
):
    """Create an instructor for a class"""
    config = initializeApp(common)
    mxlogger.info(f"Creating instructor {instructor_vup_id} for class {class_id}")
    result = cs.cs_instructor_create(
        instructor_vup_id, class_id,
        send_invite_now=send_invite_now if send_invite_now is not None else True,
        disable_env_creation=disable_env_creation if disable_env_creation is not None else True,
    )
    print_results(result, config)


@cs_app.command()
def instructor_delete(
    instructor_id: Annotated[str, Parameter(help="Instructor Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Delete an instructor"""
    initializeApp(common)
    mxlogger.info(f"Deleting instructor {instructor_id}")
    cs.cs_instructor_delete(instructor_id)
    mxlogger.info("Instructor deleted")


# ──────────────────────────────────────────
# Webhook commands
# ──────────────────────────────────────────


@cs_app.command()
def webhook_list(
    *,
    common: mxCommonOpts | None = None,
):
    """List all webhooks"""
    config = initializeApp(common)
    hooks = cs.cs_webhook_get_all()
    print_results(hooks, config)


@cs_app.command()
def webhook_get(
    webhook_id: Annotated[str, Parameter(help="Webhook Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get webhook details by ID"""
    config = initializeApp(common)
    hook = cs.cs_webhook_get(webhook_id)
    print_results(hook, config)


@cs_app.command()
def webhook_create(
    url: Annotated[str, Parameter(help="Webhook URL")],
    event: Annotated[str, Parameter(help="Webhook event type")],
    *,
    common: mxCommonOpts | None = None,
):
    """Create a webhook"""
    config = initializeApp(common)
    mxlogger.info(f"Creating webhook for event {event}")
    result = cs.cs_webhook_create(url, event)
    print_results(result, config)


@cs_app.command()
def webhook_delete(
    webhook_id: Annotated[str, Parameter(help="Webhook Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Delete a webhook"""
    initializeApp(common)
    mxlogger.info(f"Deleting webhook {webhook_id}")
    cs.cs_webhook_delete(webhook_id)
    mxlogger.info("Webhook deleted")


# ──────────────────────────────────────────
# Permalink commands
# ──────────────────────────────────────────


@cs_app.command()
def permalink_create(
    snapshot_id: Annotated[str, Parameter(help="Snapshot Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Create a permalink for a snapshot"""
    config = initializeApp(common)
    result = cs.cs_permalink_create(snapshot_id)
    print_results(result, config)


@cs_app.command()
def permalink_get(
    permalink_id: Annotated[str, Parameter(help="Permalink Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get permalink details by ID"""
    config = initializeApp(common)
    result = cs.cs_permalink_get(permalink_id)
    print_results(result, config)


# ──────────────────────────────────────────
# Utility commands
# ──────────────────────────────────────────


@cs_app.command()
def ping(
    *,
    common: mxCommonOpts | None = None,
):
    """Ping the CloudShare API"""
    config = initializeApp(common)
    result = cs.cs_ping()
    print_results(result, config)


@cs_app.command()
def region_list(
    *,
    common: mxCommonOpts | None = None,
):
    """List all regions"""
    config = initializeApp(common)
    regions = cs.cs_region_get_all()
    print_results(regions, config)


@cs_app.command()
def timezone_list(
    *,
    common: mxCommonOpts | None = None,
):
    """List all timezones"""
    config = initializeApp(common)
    zones = cs.cs_timezone_get_all()
    print_results(zones, config)


# ──────────────────────────────────────────
# Team commands
# ──────────────────────────────────────────


@cs_app.command()
def team_list(
    *,
    common: mxCommonOpts | None = None,
):
    """List all teams"""
    config = initializeApp(common)
    teams = cs.cs_team_get_all()
    print_results(teams, config)


@cs_app.command()
def team_create(
    name: Annotated[str, Parameter(help="Team name")],
    *,
    common: mxCommonOpts | None = None,
):
    """Create a team"""
    config = initializeApp(common)
    mxlogger.info(f"Creating team {name}")
    result = cs.cs_team_create(name)
    print_results(result, config)


# ──────────────────────────────────────────
# Invitation commands
# ──────────────────────────────────────────


@cs_app.command()
def invite_project_member(
    email: Annotated[str, Parameter(help="Email address")],
    project_id: Annotated[str, Parameter(help="Project Id")],
    role: Annotated[str, Parameter(help="Role (e.g. Owner, Editor, Viewer)")],
    *,
    common: mxCommonOpts | None = None,
):
    """Invite a project member"""
    config = initializeApp(common)
    mxlogger.info(f"Inviting {email} to project {project_id}")
    result = cs.cs_invite_project_member(email, project_id, role)
    print_results(result, config)


@cs_app.command()
def invite_to_poc(
    email: Annotated[str, Parameter(help="Email address")],
    topology_id: Annotated[str, Parameter(help="Topology Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Invite to a POC"""
    config = initializeApp(common)
    mxlogger.info(f"Inviting {email} to POC {topology_id}")
    result = cs.cs_invite_to_poc(email, topology_id)
    print_results(result, config)


@cs_app.command()
def login_url(
    *,
    common: mxCommonOpts | None = None,
):
    """Get login URL"""
    config = initializeApp(common)
    result = cs.cs_get_login_url()
    print_results(result, config)


# ──────────────────────────────────────────
# Analytics commands
# ──────────────────────────────────────────


@cs_app.command()
def class_guided_journey(
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get guided journey progress for a class"""
    config = initializeApp(common)
    result = cs.cs_class_guided_journey_progress(class_id)
    print_results(result, config)


@cs_app.command()
def student_guided_journey(
    student_id: Annotated[str, Parameter(help="Student Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get guided journey progress for a student"""
    config = initializeApp(common)
    result = cs.cs_student_guided_journey_progress(student_id)
    print_results(result, config)


@cs_app.command()
def shared_env_get(
    project_id: Annotated[str, Parameter(help="Project Id")],
    base_blueprint_id: Annotated[str, Parameter(help="Base blueprint Id")],
    region_id: Annotated[str, Parameter(help="Region Id")],
    class_id: Annotated[str, Parameter(help="Class Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get shared environments"""
    config = initializeApp(common)
    result = cs.cs_shared_environment_get(project_id, base_blueprint_id, region_id, class_id)
    print_results(result, config)


@cs_app.command()
def public_cloud_get(
    environment_id: Annotated[str, Parameter(help="Environment Id")],
    *,
    common: mxCommonOpts | None = None,
):
    """Get public cloud details for an environment"""
    config = initializeApp(common)
    result = cs.cs_public_cloud_get(environment_id)
    print_results(result, config)


def loadKeys(envfile):
    # load authentication keys in the following order:
    # 0. from envfile passed as argument
    # 1. from environment variables
    # 2. from cloudshare.env file in the current directory

    my_API_ID = None
    my_API_KEY = None
    if envfile:
        # Try loading from envfile
        mxlogger.info(f"Trying to load auth keys from {envfile}")
        load_dotenv(envfile)

    # Try loading then from environment
    my_API_ID = os.getenv("CLOUDSHARE_API_ID")
    my_API_KEY = os.getenv("CLOUDSHARE_API_KEY")

    # If not found in envfile or environment, try loading from cloudshare.env
    if my_API_ID is None or my_API_KEY is None:
        if os.path.exists("cloudshare.env"):
            mxlogger.info("Trying to load auth keys from cloudshare.env in current directory")
            load_dotenv("cloudshare.env")
            my_API_ID = os.getenv("CLOUDSHARE_API_ID")
            my_API_KEY = os.getenv("CLOUDSHARE_API_KEY")

    # if still no keys exit
    if my_API_ID is None or my_API_KEY is None:
        mxlogger.error(
            """CLOUDSHARE_API_ID and CLOUDSHARE_API_KEY not found.
Please create a 'cloudshare.env' file with the following content:
    CLOUDSHARE_API_ID=<your_api_id>
    CLOUDSHARE_API_KEY=<your_api_key>
Or export them as environment variables:
    export CLOUDSHARE_API_ID=<your_api_id>
    export CLOUDSHARE_API_KEY=<your_api_key>
"""
        )
        sys.exit(1)

    mxlogger.info("Auth keys loaded")
    return my_API_ID, my_API_KEY


@cs_app.command
def shell():
    commopts = mxCommonOpts()
    initializeApp(commopts)
    cs_app.interactive_shell()


# # # MAIN # # #
def main() -> None:
    """Console-script entry point."""
    cs_app()


if __name__ == "__main__":
    main()
