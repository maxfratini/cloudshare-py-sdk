
import mxcloudshare.cloudshare as cloudshare

_apiID = "API_ID"
_apiKey = "API_KEY"


def cs_set_auth_keys(api_id, api_key):
    global _apiID
    global _apiKey
    _apiID = api_id
    _apiKey = api_key


def cs_request(method, path, queryParams=None, content=None):
    res = cloudshare.req(hostname="use.cloudshare.com", method=method, apiId=_apiID, apiKey=_apiKey, path=path, queryParams=queryParams, content=content)
    if res.status // 100 != 2:
        raise Exception("{} {}".format(res.status, res.content["message"]))
    return res.content


def execute_path(machine, command):
    return cs_post("/vms/actions/executePath", {"vmId": machine["id"], "path": command})


def get_execution_status(machine, execution):
    return cs_get("vms/actions/checkExecutionStatus", {"vmId": machine["id"], "executionId": execution["executionId"]})


def cs_post(path, content=None):
    return cs_request("POST", path, content=content)


def cs_get(path, queryParams=None):
    return cs_request("GET", path, queryParams=queryParams)


def cs_put(path, queryParams=None):
    return cs_request("PUT", path, queryParams=queryParams)


def cs_delete(path, queryParams=None):
    return cs_request("DELETE", path, queryParams=queryParams)


def get_vms(envid):
    results = cs_get("envs/actions/getextended", {"envId": envid})
    vms = results["vms"]
    return vms


def env_get_status(envid):
    status = cs_get("/envs/actions/getextended", {"envId": envid})["statusText"]
    return status


# Environment related functions
def cs_env_get(env_id: str) -> dict:
    """Get environment details by ID"""
    return cs_get(f"/envs/{env_id}")


def cs_env_get_all(brief: bool = False) -> list[dict]:
    """Get all environments"""
    return cs_get(f"envs/?brief={str(brief).lower()}")


def cs_env_suspend(env_id: str) -> dict:
    """Suspend an environment"""
    return cs_put("/envs/actions/suspend", {"envId": env_id})


def cs_env_resume(env_id: str) -> dict:
    """Resume an environment"""
    return cs_put("/envs/actions/resume", {"envId": env_id})


def cs_env_delete(env_id: str) -> dict:
    """Delete an environment"""
    return cs_delete(f"/envs/{env_id}")


def cs_env_create(blueprint_id: str, policy_id: str = None, name: str = None, description: str = None) -> dict:
    """Create an environment from a blueprint"""
    payload = {
        "blueprintId": blueprint_id,
    }
    if policy_id:
        payload["policyId"] = policy_id
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description

    return cs_post("/envs/actions/create", payload)


# Blueprint related functions
def cs_blueprint_get_all() -> list[dict]:
    """Get all blueprints"""
    return cs_get("/blueprints")


def cs_blueprint_get(blueprint_id: str) -> dict:
    """Get blueprint details by ID"""
    return cs_get(f"/blueprints/{blueprint_id}")


# Policy related functions
def cs_policy_get_all() -> list[dict]:
    """Get all policies"""
    return cs_get("/policies")


def cs_policy_get(policy_id: str) -> dict:
    """Get policy details by ID"""
    return cs_get(f"/policies/{policy_id}")


# Class related functions
def cs_class_get_all() -> list[dict]:
    """Get all classes"""
    return cs_get("/class")


def cs_class_get(class_id: str) -> dict:
    """Get class details by ID"""
    return cs_get(f"/class/{class_id}")


def cs_class_create(blueprint_id: str, policy_id: str | None = None, name: str | None = None, description: str | None = None) -> dict:
    """Create a class from a blueprint"""
    payload = {
        "blueprintId": blueprint_id,
    }
    if policy_id:
        payload["policyId"] = policy_id
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description

    return cs_post("/class", payload)


def cs_class_update(class_id: str, payload: dict) -> dict:
    """Update a class"""
    return cs_put(f"/class/{class_id}", payload)


def cs_class_delete(class_id: str) -> dict:
    """Delete a class"""
    return cs_delete(f"/class/{class_id}")


# VM related functions
def cs_vm_get_all(env_id: str) -> list[dict]:
    """Get all VMs in an environment"""
    return get_vms(env_id)  # This uses the existing get_vms function


def cs_vm_execute_path(vm_id: str, path: str, args: str | None = None) -> dict:
    """Execute a command on a VM"""
    payload = {"vmId": vm_id, "path": path}
    if args:
        payload["args"] = args

    return cs_post("/vms/actions/executePath", payload)


# General purpose helper for any API call
def cs_api_call(method: str, path: str, payload: dict | None = None) -> dict | list[dict]:
    """Make a generic API call to CloudShare"""
    if method.upper() == "GET":
        return cs_get(path)
    elif method.upper() == "POST":
        return cs_post(path, payload or {})
    elif method.upper() == "PUT":
        return cs_put(path, payload or {})
    elif method.upper() == "DELETE":
        return cs_delete(path)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
