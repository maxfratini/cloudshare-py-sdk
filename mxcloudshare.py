#!/usr/bin/env python3

#

import json
import logging
import os
import time
from collections import namedtuple
from enum import Enum
#####
# from typing import Tuple
from typing import List, Optional

# from traceback import print_tb
import attr
import pandas as pd
import typer
from dotenv import load_dotenv
from rich import box, print, print_json
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

import cloudshare
from typerlogging.TyperLogging import TyperLogging

logger = logging.getLogger(__name__)


# import sys


# ##############
# Global objects
#


class OutFormat(str, Enum):
    csv_fmt = "csv"
    json_fmt = "json"
    table_fmt = "table"
    card_fmt = "card"


def print_results(results, output_format):
    if output_format == OutFormat.table_fmt:
        print_as_table(results)
    elif output_format == OutFormat.json_fmt:
        import json

        json_results = json.dumps(results)
        print_json(json_results)
    elif output_format == OutFormat.csv_fmt:
        logger.info("Csv not implemented yet")
    elif output_format == OutFormat.card_fmt:
        for r in results:
            print_as_table(r)


globalconf = {
    "outputformat": OutFormat.json_fmt,
    "tablewidth": 80,
    "API_ID": None,
    "API_KEY": None,
}

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, name="mxCloudShare", help="Cloudshare automation tool")

#
# END Global objects
# ################




# CartItemType = namedtuple(
#     "CartItemType", ["BASED_ON_BP", "ADD_TEMPLATE_VM"])(1, 2)
# TemplateType = namedtuple("TemplateType", ["BLUEPRINT", "VM"])(0, 1)


# def example1_execute_command_on_machine():
#     env = get_first_env()
#     machine = get_first_machine(env)
#     execution = execute_path(machine, "echo hello world")
#     execution_status = get_execution_status(machine, execution)
#     while not execution_status['success']:
#         time.sleep(5)
#         execution_status = get_execution_status(machine, execution)
#     logger.info("Execution finished! output:\n%s" % execution_status['standardOutput'])


# def example2_create_custom_environment():
#     project_id = get_first_project_id()
#     miami_region_id = get_miami_region_id()
#     template_vm_id = get_first_template_vm_id()
#     name = create_environment_name()
#     env = create_environment(name, project_id, miami_region_id, template_vm_id)
#     logger.info("New environment ID: " + env["environmentId"])
#     logger.info("New environment Name: " + name)
#     logger.info("(This new environment is preparing, to avoid unwanted charges log")
#     "to use.cloudshare.com and delete the environment)"


# def get_first_project_id():
#     projects = cs_get(projects")
#     if len(projects) == 0:
#         raise Exception("No projects found")
#     return projects[0]["id"]


# def get_miami_region_id():
#     regions = [r for r in cs_get(regions") if r["name"] == "Miami"]
#     if len(regions) == 0:
#         raise Exception("'Miami' region not found")
#     return regions[0]["id"]


# def get_first_template_vm_id():
#     templates = cs_get("templates", {
#         "templateType": TemplateType.VM,
#         "take": 1
#     })
#     if len(templates) == 0:
#         raise Exception("No VM templates found")
#     return templates[0]["id"]


# def create_environment(name, projectId, regionId, templateVmId):
#     return post("envs", {
#         "environment": {
#                 "name": name,
#                 "description": "Environment created from API example",
#                 "projectId": projectId,
#                 "policyId": None,
#                 "regionId": regionId
#                 },
#         "itemsCart": [
#             {
#                 "type": CartItemType.ADD_TEMPLATE_VM,
#                 "name": "My Virtual Machine",
#                 "description": "My Virtual Machine",
#                 "templateVmId": templateVmId
#             }
#         ]
#     })


# def create_environment_name():
#     return "API Example Environment - " + get_timestamp()


# def get_first_env():
#     envs = cs_get('envs/')
#     if len(envs) == 0:
#         raise Exception("You don't have any environments!")
#     if get_env_status(envs[0]) != "Ready":
#         raise Exception("Your first environment is not running!")
#     logger.info("I found the \"%s\" environment." % envs[0]['name'])
#     return envs[0]

# def get_first_machine(env):
#     machines = cs_get('envs/actions/machines/', {'eid': env['id']})
#     if len(machines) == 0:
#         raise Exception("Your first environment doesn't have any machines!")
#     logger.info('''I'm going to execute "echo hello world" on the machine "%s" in environment "%s" .''' % (
#         machines[0]['name'], env['name']))
#     return machines[0]


def execute_path(machine, command):
    return cs_post("/vms/actions/executePath", {"vmId": machine["id"], "path": command})


def get_execution_status(machine, execution):
    logger.info("polling execution status...")
    return cs_get("vms/actions/checkExecutionStatus", {"vmId": machine["id"], "executionId": execution["executionId"]})


def cs_post(path, content=None):
    return cs_request("POST", path, content=content)


def cs_get(path, queryParams=None):
    return cs_request("GET", path, queryParams=queryParams)

def cs_put(path, queryParams=None):
    return cs_request("PUT", path, queryParams=queryParams)

def cs_delete(path, queryParams=None):
    return cs_request("DELETE", path, queryParams=queryParams)


def cs_request(method, path, queryParams=None, content=None):
    res = cloudshare.req(hostname="use.cloudshare.com", method=method, apiId=globalconf["API_ID"], apiKey=globalconf["API_KEY"], path=path, queryParams=queryParams, content=content)
    if res.status // 100 != 2:
        raise Exception("{} {}".format(res.status, res.content["message"]))
    return res.content


def get_timestamp():
    return str(int(time.time()))


# ################################################################################
def df_to_table(
    pandas_dataframe: pd.DataFrame,
    rich_table: Table,
    show_index: bool = False,
    index_name: Optional[str] = None,
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



def get_vms(envid: Annotated[str, typer.Option(help="Environment Id")]):
    results = cs_get("envs/actions/getextended", {"envId": envid})
    vms = results["vms"]
    return vms


@app.command()
def env_show_all():
    """
    Show all environments
    """
    envs = cs_get("envs/")
    if len(envs) == 0:
        logger.info("No environments found")

    i = 0
    for e in envs:
        i += 1
        e["status"] = env_get_status(e.get('id', ''))
        e["index"] = i

    print_results(envs, globalconf["outputformat"])




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
        machines = get_vms(envId)
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
                    logger.debug(f"VM {m['name']} failed condition: {property_name} is {m[property_name]}, let's wait more...")
                    logger.debug(f"VM is {json.dumps(m, indent=2, sort_keys=True)}")
                    stillWorking = True
                    # stop checking at first condition failed and wait next retry
                    break
            # stop checking as soon as a VM failed, and wait next retry
            if stillWorking:
                break

        # if still working, wait for delay_secs before next retry
        if stillWorking:
            logger.info(f"Polling status #{retries}, waiting {delay_secs} seconds...")
            time.sleep(delay_secs)

    # When we get here, either job completed (stillWorking=False) or we timed out (stillWorking=True)
    if stillWorking:
        logger.debug("Timed out waiting for environment to reach desired state")
        return False
    else:
        logger.debug("Environment reached desired state")
        return True


@app.command()
def env_suspend(envId: Annotated[str, typer.Option(help="Environment Id")]):
    """
    Suspend an environment
    """
    cs_put("/envs/actions/suspend", {"envId": envId})
    logger.info("Suspend Started")

    checks = [
        {"property": "statusText", "check_fn": lambda x: x == "Suspended"}
    ]
    completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
    if completed:
        logger.info("Suspend completed!")
    else:
        logger.info("Timed out waiting for environment to reach Suspended state")





@app.command()
def env_delete(envId: Annotated[str, typer.Option(help="Environment Id")], force: Annotated[bool, typer.Option(help="Force deletion")] = False):
    """
    Delete an environment
    """
    cs_delete("/envs/" + str(envId) + "")
    logger.info("Delete Started!")

    checks = [
        {"property": "internalIp", "check_fn": lambda x: x is None}
    ]
    completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
    if completed:
        logger.info("Delete completed!")
    else:
        logger.info("Timed out waiting for environment to reach Suspended state")




@app.command()
def env_resume(envId: Annotated[str, typer.Option(help="Environment Id")]):
    """
    Resume a paused environment
    """
    cs_put("/envs/actions/resume", {"envId": envId})
    logger.info("Resume Started")

    checks = [
        {"property": "statusText", "check_fn": lambda x: x == "Running"}
    ]
    completed = env_wait_condition(envId, checks, delay_secs=6, max_retry=20)
    if completed:
        logger.info("Resume completed!")
    else:
        logger.info("Timed out waiting for environment to reach Resumed state")




@app.command()
def env_get_vms_info(
    envid: Annotated[str, typer.Option(help="Environment Id")],
    field: Annotated[Optional[List[str]], typer.Option(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[Optional[bool], typer.Option(help="Show all available attributes")] = False,
):
    """
    Show all vms info for an environment
    """
    machines = get_vms(envid)

    if availfields:
        all_keys = set().union(*(d.keys() for d in machines))
        logger.info(all_keys)
        exit()

    if len(field) > 0:
        for m in machines:
            unwanted = set(m) - set(field)
            for unwanted_key in unwanted:
                del m[unwanted_key]

    print_results(machines, globalconf["outputformat"])


@app.command()
def env_get_info(
    envid: Annotated[str, typer.Option(help="Environment Id")],
    field: Annotated[Optional[List[str]], typer.Option(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[Optional[bool], typer.Option(help="Show all available attributes")] = False,
):
    """
    Show info for an environment
    """

    e = cs_get("/envs/" + str(envid) + "")

    if availfields:
        all_keys = set().union(*(d.keys() for d in e))
        logger.info(all_keys)
        exit()

    if len(field) > 0:
        for m in e:
            unwanted = set(m) - set(field)
            for unwanted_key in unwanted:
                del m[unwanted_key]

    print_results(e, globalconf["outputformat"])



@app.command()
def blueprint_list(
    field: Annotated[Optional[List[str]], typer.Option(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[Optional[bool], typer.Option(help="Show all available attributes")] = False,
):
    """
    Show all available blueprints
    """
    blueprints = cs_get("/blueprints")

    if availfields:
        all_keys = set().union(*(d.keys() for d in blueprints))
        logger.info(all_keys)
        exit()

    if len(field) > 0:
        for b in blueprints:
            unwanted = set(b) - set(field)
            for unwanted_key in unwanted:
                del b[unwanted_key]

    print_results(blueprints, globalconf["outputformat"])


@app.command()
def policy_list(
    field: Annotated[Optional[List[str]], typer.Option(help="Attribute to show (repeat for multiple attributes)")] = [],
    availfields: Annotated[Optional[bool], typer.Option(help="Show all available attributes")] = False,
):
    """
    Show all available policies
    """
    policies = cs_get("/policies")

    if availfields:
        all_keys = set().union(*(d.keys() for d in policies))
        logger.info(all_keys)
        exit()

    if len(field) > 0:
        for p in policies:
            unwanted = set(p) - set(field)
            for unwanted_key in unwanted:
                del p[unwanted_key]

    print_results(policies, globalconf["outputformat"])


@app.command()
def env_create(
    blueprint_id: Annotated[str, typer.Option(help="Blueprint ID to create environment from")],
    policy_id: Annotated[str, typer.Option(help="Policy ID to use")] = None,
    name: Annotated[str, typer.Option(help="Name for the new environment")] = None,
    description: Annotated[str, typer.Option(help="Description for the new environment")] = None,
    count: Annotated[int, typer.Option(help="Number of environments to create")] = 1,
):
    """
    Create one or more environments from a blueprint
    """
    results = []
    for i in range(count):
        payload = {
            "blueprintId": blueprint_id,
        }

        if policy_id:
            payload["policyId"] = policy_id
        if name:
            payload["name"] = f"{name}-{i+1}" if count > 1 else name
        if description:
            payload["description"] = description

        result = cs_get("/envs/actions/create", payload)
        results.append(result)

    print_results(results, globalconf["outputformat"])


@app.command()
def class_create(
    blueprint_id: Annotated[str, typer.Option(help="Blueprint ID to create class from")],
    policy_id: Annotated[str, typer.Option(help="Policy ID to use")] = None,
    name: Annotated[str, typer.Option(help="Base name for the new classes")] = None,
    description: Annotated[str, typer.Option(help="Description for the new classes")] = None,
    count: Annotated[int, typer.Option(help="Number of classes to create")] = 1,
):
    """
    Create one or more classes with numbered suffixes
    """
    logger.info(f"Creating {count} classes")
    results = []
    for i in range(count):
        logger.info(f"Creating class {i+1}")
        payload = {"blueprintId": blueprint_id}
        if policy_id:
            payload["policyId"] = policy_id
        if name:
            payload["name"] = f"{name}-{i+1}"
        if description:
            payload["description"] = description

        result = cs_post("/class", payload)
        results.append(result)

    print_results(results, globalconf["outputformat"])


@app.command()
def class_clone(
    class_id: Annotated[str, typer.Option(help="Class ID to clone from")],
    count: Annotated[int, typer.Option(help="Number of clones to create")] = 1,
    name_suffix: Annotated[str, typer.Option(help="Base suffix for the cloned classes")] = "",
):
    """
    Clone an existing class multiple times with numbered suffixes
    """
    logger.info(f"Cloning class {class_id} {count} times")

    # Get original class details
    original_class = cs_get(f"/class/{class_id}")
    results = []

    for i in range(count):
        logger.info(f"Creating clone {i+1}")
        payload = original_class.copy()
        payload["name"] = f"{original_class['name']}{name_suffix}{i+1}"
        result = cs_post("/class", payload)
        results.append(result)

    print_results(results, globalconf["outputformat"])


@app.command()
def class_setstatus(
    class_pattern: Annotated[str, typer.Option(help="Regex pattern to match class name")],
    status: Annotated[str, typer.Option(help="Set status of the class ACTIVE|SUSPENDED")] = "ACTIVE",
    by_id: Annotated[bool, typer.Option(help="Match pattern against class IDs instead of names")] = False,
):
    """
    Suspend or resume classes matching the specified regex pattern
    """
    import re

    status = status.upper()
    action = "resuming" if status == "ACTIVE" else "suspending"
    logger.info(f"{action.capitalize()} classes matching pattern: {class_pattern}")

    # Get all classes
    classes = cs_get("/class")
    pattern = re.compile(class_pattern)

    results = []
    for class_item in classes:
        match_field = class_item["id"] if by_id else class_item["name"]
        if pattern.search(match_field):
            logger.info(f"{action.capitalize()} class {class_item['id']} ({class_item['name']})")
            payload = {"status": "active" if status else "suspended"}
            result = cs_put(f"/class/{class_item['id']}", payload)
            results.append(result)

    if not results:
        logger.info("No classes found matching the pattern")
        return

    print_results(results, globalconf["outputformat"])

@app.command()
def class_show_all():
    classes = cs_get("class/")

    if len(classes) == 0:
        logger.info("No classes found")
    i = 0
    for c in classes:
        i += 1
        c["status"] = env_get_status(c.get('id', ''))
        c["index"] = i

    print_results(classes, globalconf["outputformat"])

@app.command()
def class_get(class_id):
    cls = cs_get("class/{}".format(class_id))
    logger.info("class name: {0}".format(cls["name"]))



@app.command()
def class_delete(
    class_pattern: Annotated[str, typer.Option(help="Regex pattern to match class name or ID")],
    by_id: Annotated[bool, typer.Option(help="Match pattern against class IDs instead of names")] = False,
):
    """
    Delete classes matching the specified regex pattern (matches against names by default)
    """
    import re

    logger.info(f"Deleting classes matching pattern: {class_pattern}")

    # Get all classes
    classes = cs_get("/class")
    pattern = re.compile(class_pattern)

    results = []
    for class_item in classes:
        match_field = class_item["id"] if by_id else class_item["name"]
        if pattern.search(match_field):
            if class_item.get("status") != "deleted":
                logger.info(f"Deleting class {class_item['id']} ({class_item['name']})")
                result = cs_delete(f"/class/{class_item['id']}")
                results.append({"id": class_item["id"], "name": class_item["name"], "status": "deleted"})
            else:
                logger.info(f"Skipping class {class_item['id']} ({class_item['name']}) - already deleted")
    if not results:
        logger.info("No classes found matching the pattern")
        return

    print_results(results, globalconf["outputformat"])


@app.command()
def class_list(
    fields: Annotated[str, typer.Option(help="Comma-separated list of fields to display")] = "id,name", pattern: Annotated[str, typer.Option(help="Regex pattern to match class names")] = ".*"
):
    """
    List all classes with specified fields (defaults to id and name)
    """
    import re
    logger.info("Listing classes")
    results = cs_get("/class")
    pattern = re.compile(pattern)
    filtered_results = []
    field_list = fields.split(",")

    for item in results:
        if pattern.search(item["name"]):
            item_filtered_fields = {field: item[field] for field in field_list if field in item}
            filtered_results.append(item_filtered_fields)
    print_results(filtered_results, globalconf["outputformat"])


def env_get_status(envid: Annotated[str, typer.Option(help="Environment Id")]):
    status = cs_get("/envs/actions/getextended", {"envId": envid})["statusText"]
    logger.debug(f"Env status is: {status}")
    return status


def loadKeys(envfile):
    # load authentication keys in the following order:
    # 0. from envfile passed as argument
    # 1. from environment variables
    # 2. from cloudshare.env file in the current directory

    my_API_ID = None
    my_API_KEY = None
    if envfile:
        # Try loading from envfile
        logger.info(f"Trying to load auth keys from {envfile}")
        load_dotenv(envfile)

    # Try loading then from environment
    my_API_ID = os.getenv('CLOUDSHARE_API_ID')
    my_API_KEY = os.getenv('CLOUDSHARE_API_KEY')

    # If not found in envfile or environment, try loading from cloudshare.env
    if my_API_ID is None or my_API_KEY is None:
        if os.path.exists('cloudshare.env'):
            logger.info("Trying to load auth keys from cloudshare.env in current directory")
            load_dotenv('cloudshare.env')
            my_API_ID = os.getenv('CLOUDSHARE_API_ID')
            my_API_KEY = os.getenv('CLOUDSHARE_API_KEY')

    # if still no keys exit
    if my_API_ID is None or my_API_KEY is None:
        logger.info('''
CLOUDSHARE_API_ID and CLOUDSHARE_API_KEY not found.
Please create a 'cloudshare.env' file with the following content:
    CLOUDSHARE_API_ID=<your_api_id>
    CLOUDSHARE_API_KEY=<your_api_key>
Or export them as environment variables:
    export CLOUDSHARE_API_ID=<your_api_id>
    export CLOUDSHARE_API_KEY=<your_api_key>
        ''')
        exit(1)

    logger.info("Auth keys loaded")
    return my_API_ID, my_API_KEY


# ### App callback for common options
@app.callback()
def main(
    outformat: str = typer.Option(OutFormat.json_fmt, "--outformat", "-o", help="Set output format."),
    tablewidth: int = typer.Option(80, "--tablewidth", "-w", help="Set table output width."),
    keyfile: str = typer.Option(None, "--keyfile", "-k", help="Path to CloudShare authentication keys file."),
    loglevel: str = typer.Option("INFO", help="Set the logging level"),
    logfile: Optional[str] = typer.Option(None, help="Path to save the log file."),
):
    """
    Global Options
    """

    TyperLogging.setup_from_typer(logfile, loglevel)

    # setLogging(loglevel, logfile)
    logger.info("LogLevel is set to %s", logging.getLevelName(logging.getLogger().getEffectiveLevel()))

    globalconf["outputformat"] = outformat
    globalconf["tablewidth"] = tablewidth

    # Load auth keys
    _API_ID, _API_KEY = loadKeys(keyfile)
    logger.debug(f"Loaded API_ID: {_API_ID} and API_KEY: {_API_KEY}")

    globalconf["API_ID"] = _API_ID
    globalconf["API_KEY"] = _API_KEY



# # # MAIN # # #
if __name__ == "__main__":
    app()
