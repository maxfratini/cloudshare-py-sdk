import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated

import pandas as pd
from cyclopts import App, Parameter
from dotenv import load_dotenv
from rich import box, print_json
from rich.console import Console
from rich.table import Table

from mxcloudshare import mxcloudshare as cs
from mxcloudshare.mxutils import mxLogging

mxlogger = mxLogging.getLogger(__name__)

# ##############
# Global objects
#
cs_app = App(name="mxCloudShare", help="Cloudshare automation tool")


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


globalconf = {
    "outputformat": OutFormat.json_fmt,
    "tablewidth": 80,
    "API_ID": None,
    "API_KEY": None,
}


def print_results(results, output_format):
    if output_format == OutFormat.table_fmt:
        print_as_table(results)
    elif output_format == OutFormat.json_fmt:
        json_results = json.dumps(results)
        print_json(json_results)
    elif output_format == OutFormat.csv_fmt:
        mxlogger.info(">>> Csv not implemented yet <<<")
    elif output_format == OutFormat.card_fmt:
        for r in results:
            print_as_table(r)


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


# Initialize the application
def initializeApp(commopts: mxCommonOpts | None):
    global globalconf

    # cyclopts leaves the dataclass as None when none of its options were given
    # on the command line, so fall back to the declared defaults.
    if commopts is None:
        commopts = mxCommonOpts()

    mxlogger.setup_mxLogger(log_file=commopts.logfile, log_level=commopts.loglevel)
    if commopts.loglevel.upper() in ["INFO", "DEBUG"]:
        mxlogger.info("LogLevel is set to %s", logging.getLevelName(logging.getLogger().getEffectiveLevel()))

    globalconf["outputformat"] = commopts.outformat
    globalconf["tablewidth"] = commopts.tablewidth

    # Load auth keys
    _API_ID, _API_KEY = loadKeys(commopts.keyfile)
    mxlogger.debug(f"Loaded API_ID: {_API_ID} and API_KEY: {_API_KEY}")

    globalconf["API_ID"] = _API_ID
    globalconf["API_KEY"] = _API_KEY

    cs.cs_set_auth_keys(_API_ID, _API_KEY)


def get_timestamp():
    return str(int(time.time()))


# ################################################################################
def df_to_table(
    pandas_dataframe: pd.DataFrame,
    rich_table: Table,
    show_index: bool = False,
    index_name: str | None = None,
) -> Table:
    """Convert a pandas.DataFrame obj into a rich.Table obj.
    Args:
        pandas_dataframe (DataFrame): A Pandas DataFrame to be converted to a rich Table.
        rich_table (Table): A rich Table that should be populated by the DataFrame values.
        show_index (bool): Add a column with a row count to the table. Defaults to True.
        index_name (str, optional): The column name to give to the index column. Defaults to None, showing no value.
    Returns:
        Table: The rich Table instance passed, populated with the DataFrame values."""

    if show_index:
        index_name = str(index_name) if index_name else ""
        rich_table.add_column(index_name)

    for column in pandas_dataframe.columns:
        rich_table.add_column(str(column))

    for index, value_list in enumerate(pandas_dataframe.values.tolist()):
        row = [str(index)] if show_index else []
        row += [str(x) for x in value_list]
        rich_table.add_row(*row)

    return rich_table


def show_results(data, title=None):
    """Display results in a formatted table using global settings

    Args:
        data: Data to display (list or dict)
        title: Optional title for the table
    """
    console = Console(width=globalconf["tablewidth"])

    if isinstance(data, dict):
        data = [data]

    df = pd.json_normalize(data)
    table = Table(show_header=True, header_style="bold", title=title)
    table = df_to_table(df, table)
    table.row_styles = ["none", "dim"]
    table.box = box.SIMPLE_HEAD

    console.print(table)

    return len(data)


def print_as_table(d):
    df = pd.json_normalize(d)
    # Initiate a Table instance to be modified
    table = Table(show_header=True, header_style="bold")
    # Modify the table instance to have the data from the DataFrame
    table = df_to_table(df, table)
    # Update the style of the table
    table.row_styles = ["none", "dim"]
    table.box = box.SIMPLE_HEAD
    console = Console(width=globalconf["tablewidth"])
    console.print(table)


@cs_app.command()
def env_show_all(
    common: mxCommonOpts | None = None,
):
    """
    Show all environments
    """
    initializeApp(common)

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

    print_results(brief_envs, globalconf["outputformat"])


def env_wait_condition(envId: str, checks: str, delay_secs: int = 3, max_retry: int = 10):
    """
    Poll an environment for a status
    envid: environment id
    conditions: list of dicts with conditions to check for. dict should contain:
        - property: property of vms to check for
        - check_fn: function to execute against property that must be true
    delay_secs: seconds to wait between polls
    max_retry: maximum number of retries
    """
    stillWorking = True
    retries = 0
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
                    # stop checking at first condition failed and wait next retry
                    break
            # stop checking as soon as a VM failed, and wait next retry
            if stillWorking:
                break

        # if still working, wait for delay_secs before next retry
        if stillWorking:
            mxlogger.info(f"Polling status #{retries}, waiting {delay_secs} seconds...")
            time.sleep(delay_secs)

    # When we get here, either job completed (stillWorking=False) or we timed out (stillWorking=True)
    if stillWorking:
        mxlogger.debug("Timed out waiting for environment to reach desired state")
        return False
    else:
        mxlogger.debug("Environment reached desired state")
        return True


#
@cs_app.command()
def env_suspend(
    envId_list: Annotated[list[str], Parameter(name=["--envId", "-e"], negative=False)],
    *,
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
        # Check if the environment is in a state that can be suspended
        status = cs.env_get_status(envId)
        if status != EnvStatus.ready:
            mxlogger.info(f"Environment {envId} is not in a state that can be suspended (current status: {status})")
            continue
        # Suspend the environment
        cs.cs_env_suspend(envId)

        mxlogger.info("Suspend Started")
        # Wait for the environment to reach the desired state
        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
        if completed:
            mxlogger.info(f"Suspend of environment {envId} completed!")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Suspended state")


#
@cs_app.command()
def env_delete(
    envId_list: Annotated[list[str], Parameter(name=["--envid", "-e"], negative=False)],
    *,
    common: mxCommonOpts | None = None,
):
    """Delete an environment
    Args:
        envId_list (Annotated[List[str], required): Environment Id, repeat multiple time for list of ids.
    """
    common = initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Deleted"}]

    for envId in envId_list:
        mxlogger.info(f"Deleting environment {envId}")
        # Check if the environment is in a state that can be deleted
        status = cs.env_get_status(envId)
        if status == EnvStatus.deleted:
            mxlogger.info(f"Environment {envId} is not in a state that can be deleted (current status: {status})")
            continue
        # Delete the environment
        cs.cs_env_delete(envId)
        mxlogger.info("Delete Started!")
        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
        if completed:
            mxlogger.info(f"Delete of environment {envId} completed!")
        else:
            mxlogger.info(f"Timed out waiting for environment {envId} to reach Deleted state")


#
@cs_app.command()
def env_resume(
    envId_list: Annotated[list[str], Parameter(name=["--envid", "-e"], negative=False)],
    *,
    common: mxCommonOpts | None = None,
):
    """Resume a paused environment
    Args:
        envId_list (Annotated[List[str], required): Environment Id, repeat multiple time for list of ids.
    """
    common = initializeApp(common)

    checks = [{"property": "statusText", "check_fn": lambda x: x == "Running"}]

    for envId in envId_list:
        mxlogger.info(f"Resuming environment {envId}")
        # Check if the environment is in a state that can be resumed
        status = cs.env_get_status(envId)
        if status != EnvStatus.suspended:
            mxlogger.info(f"Environment {envId} is not in a state that can be resumed (current status: {status})")
            continue
        # Resume the environment
        cs.cs_env_resume(envId)
        mxlogger.info("Resume Started")

        completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
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
    initializeApp(common)

    machines = cs.get_vms(envid)

    if availfields:
        all_keys = set().union(*(d.keys() for d in machines))
        mxlogger.info(all_keys)
        sys.exit()

    if len(field) > 0:
        for m in machines:
            unwanted = set(m) - set(field)
            for unwanted_key in unwanted:
                del m[unwanted_key]

    print_results(machines, globalconf["outputformat"])


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
    initializeApp(common)

    e = cs.cs_env_get(envid)

    if availfields:
        all_keys = set().union(*(d.keys() for d in e))
        mxlogger.info(all_keys)
        sys.exit()

    if len(field) > 0:
        for m in e:
            unwanted = set(m) - set(field)
            for unwanted_key in unwanted:
                del m[unwanted_key]

    print_results(e, globalconf["outputformat"])


@cs_app.command()
def blueprint_list(
    field: Annotated[list[str] | None, Parameter(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[bool | None, Parameter(help="Show all available attributes")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Show all available blueprints
    """

    initializeApp(common)

    blueprints = cs.cs_blueprint_get_all()

    if availfields:
        all_keys = set().union(*(d.keys() for d in blueprints))
        mxlogger.info(all_keys)
        sys.exit()

    if len(field) > 0:
        for b in blueprints:
            unwanted = set(b) - set(field)
            for unwanted_key in unwanted:
                del b[unwanted_key]

    print_results(blueprints, globalconf["outputformat"])


@cs_app.command()
def policy_list(
    field: Annotated[list[str] | None, Parameter(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[bool | None, Parameter(help="Show all available attributes")] = False,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Show all available policies
    """
    initializeApp(common)

    policies = cs.cs_policy_get_all()

    if availfields:
        all_keys = set().union(*(d.keys() for d in policies))
        mxlogger.info(all_keys)
        sys.exit()

    if len(field) > 0:
        for p in policies:
            unwanted = set(p) - set(field)
            for unwanted_key in unwanted:
                del p[unwanted_key]

    print_results(policies, globalconf["outputformat"])


@cs_app.command()
def env_create(
    blueprint_id: Annotated[str, Parameter(help="Blueprint ID to create environment from")],
    policy_id: Annotated[str, Parameter(help="Policy ID to use")] = None,
    name: Annotated[str, Parameter(help="Name for the new environment")] = None,
    description: Annotated[str, Parameter(help="Description for the new environment")] = None,
    count: Annotated[int, Parameter(help="Number of environments to create")] = 1,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Create one or more environments from a blueprint
    """
    initializeApp(common)

    results = []
    for i in range(count):
        result = cs.cs_env_create(blueprint_id, policy_id, f"{name}-{i+1}", description)
        results.append(result)

    print_results(results, globalconf["outputformat"])


@cs_app.command()
def class_create(
    blueprint_id: Annotated[str, Parameter(help="Blueprint ID to create class from")],
    policy_id: Annotated[str, Parameter(help="Policy ID to use")] = None,
    name: Annotated[str, Parameter(help="Base name for the new classes")] = None,
    description: Annotated[str, Parameter(help="Description for the new classes")] = None,
    count: Annotated[int, Parameter(help="Number of classes to create")] = 1,
    *,
    common: mxCommonOpts | None = None,
):
    """
    Create one or more classes with numbered suffixes
    """
    initializeApp(common)

    mxlogger.info(f"Creating {count} classes")
    results = []
    for i in range(count):
        mxlogger.info(f"Creating class {i+1}")
        result = cs.cs_class_create(blueprint_id, policy_id, f"{name}-{i+1}", description)
        results.append(result)

    print_results(results, globalconf["outputformat"])


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
    initializeApp(common)

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

    print_results(results, globalconf["outputformat"])


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
    initializeApp(common)

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

    print_results(results, globalconf["outputformat"])


@cs_app.command()
def class_show_all(
    *,
    common: mxCommonOpts | None = None,
):
    initializeApp(common)

    classes = cs.cs_class_get_all()

    if len(classes) == 0:
        mxlogger.info("No classes found")
    # i = 0
    # for c in classes:
    #     i += 1
    #     c["status"] = cs.env_get_status(c.get("id", ""))
    #     c["index"] = i

    print_results(classes, globalconf["outputformat"])


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
    initializeApp(common)

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

    print_results(results, globalconf["outputformat"])


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

    initializeApp(common)

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
    print_results(filtered_results, globalconf["outputformat"])


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
