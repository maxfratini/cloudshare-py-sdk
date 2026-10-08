
import dataclasses

import mxcloudshare.cloudshare as cloudshare


@dataclasses.dataclass
class _AuthConfig:
    """Internal config holding CloudShare API credentials.

    Mutated by cs_set_auth_keys; read by cs_request.
    """
    api_id: str = "API_ID"
    api_key: str = "API_KEY"


_config = _AuthConfig()

# Backward-compat module-level aliases for any external code that
# imported these names directly.  Kept in sync by cs_set_auth_keys.
_apiID = _config.api_id
_apiKey = _config.api_key


def cs_set_auth_keys(api_id, api_key):
    global _apiID, _apiKey
    _config.api_id = api_id
    _config.api_key = api_key
    _apiID = api_id
    _apiKey = api_key


def cs_request(method, path, queryParams=None, content=None):
    res = cloudshare.req(
        hostname="use.cloudshare.com",
        method=method,
        apiId=_config.api_id,
        apiKey=_config.api_key,
        path=path,
        queryParams=queryParams,
        content=content,
    )
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


# Environment lifecycle helpers
def cs_env_extend(env_id: str) -> dict:
    """Extend an environment's duration"""
    return cs_put("/envs/actions/extend", {"envId": env_id})


def cs_env_revert(env_id: str, snapshot_id: str | None = None) -> dict:
    """Revert an environment to a snapshot"""
    params = {"envId": env_id}
    if snapshot_id is not None:
        params["snapshotId"] = snapshot_id
    return cs_put("/envs/actions/revert", params)


def cs_env_postpone_inactivity(env_id: str) -> dict:
    """Postpone inactivity timeout for an environment"""
    return cs_put("/envs/actions/postponeinactivity", {"envId": env_id})


# Snapshot helpers
def cs_snapshot_get(snapshot_id: str) -> dict:
    """Get snapshot details by ID"""
    return cs_get(f"/snapshots/{snapshot_id}")


def cs_snapshot_get_for_env(env_id: str) -> dict:
    """Get snapshots for an environment"""
    return cs_get("/snapshots/actions/getforenv", {"envId": env_id})


def cs_snapshot_take(env_id: str, name: str, set_as_default: bool | None = None,
                     description: str | None = None,
                     new_blueprint_name: str | None = None,
                     other_blueprint_id: str | None = None) -> dict:
    """Take a snapshot of an environment"""
    payload = {
        "envId": env_id,
        "name": name,
    }
    if set_as_default is not None:
        payload["setAsDefault"] = set_as_default
    if description is not None:
        payload["description"] = description
    if new_blueprint_name is not None:
        payload["newBlueprintName"] = new_blueprint_name
    if other_blueprint_id is not None:
        payload["otherBlueprintId"] = other_blueprint_id
    return cs_post("/snapshots/actions/takesnapshot", payload)


def cs_snapshot_mark_default(snapshot_id: str) -> dict:
    """Mark a snapshot as the default for its blueprint"""
    return cs_put("/snapshots/actions/markdefault", {"id": snapshot_id})


# VM helpers
def cs_vm_reboot(vm_id: str) -> dict:
    """Reboot a VM"""
    return cs_put("/vms/actions/reboot", {"vmId": vm_id})


def cs_vm_revert(vm_id: str, snapshot_id: str | None = None) -> dict:
    """Revert a VM to a snapshot"""
    params = {"vmId": vm_id}
    if snapshot_id is not None:
        params["snapshotId"] = snapshot_id
    return cs_put("/vms/actions/revert", params)


def cs_vm_delete(vm_id: str) -> dict:
    """Delete a VM"""
    return cs_delete(f"/vms/{vm_id}")


def cs_vm_edit_hardware(vm_id: str, payload: dict) -> dict:
    """Edit VM hardware (numCpus, memorySizeMBs, diskSizeGBs)"""
    body = {"vmId": vm_id}
    body.update(payload)
    return cs_request("PUT", "/vms/actions/editvmhardware", content=body)


def cs_vm_get_remote_access_file(vm_id: str,
                                  desktop_width: int | None = None,
                                  desktop_height: int | None = None) -> dict:
    """Get remote access file for a VM"""
    params = {"vmId": vm_id}
    if desktop_width is not None:
        params["desktopWidth"] = desktop_width
    if desktop_height is not None:
        params["desktopHeight"] = desktop_height
    return cs_get("/vms/actions/getremoteaccessfile", params)


# Project helpers
def cs_project_get_all() -> list[dict]:
    """Get all projects"""
    return cs_get("/projects")


def cs_project_blueprints_get_all(project_id: str,
                                   region_id: str | None = None,
                                   default_snapshot: str | None = None) -> list[dict]:
    """Get blueprints for a project"""
    params = {}
    if region_id is not None:
        params["regionId"] = region_id
    if default_snapshot is not None:
        params["defaultSnapshot"] = default_snapshot
    return cs_get(f"/projects/{project_id}/blueprints", params or None)


def cs_project_policies_get_all(project_id: str) -> list[dict]:
    """Get policies for a project"""
    return cs_get(f"/projects/{project_id}/policies")


# General purpose helper for any API call
def cs_api_call(method: str, path: str, payload: dict | None = None, queryParams: dict | None = None) -> dict | list[dict]:
    """Make a generic API call to CloudShare"""
    method_upper = method.upper()
    if method_upper == "GET":
        return cs_request("GET", path, queryParams=queryParams)
    elif method_upper == "POST":
        return cs_request("POST", path, queryParams=queryParams, content=payload or {})
    elif method_upper == "PUT":
        return cs_request("PUT", path, queryParams=queryParams, content=payload)
    elif method_upper == "DELETE":
        return cs_request("DELETE", path, queryParams=queryParams)
    elif method_upper == "PATCH":
        return cs_request("PATCH", path, queryParams=queryParams, content=payload)
    elif method_upper == "OPTIONS":
        return cs_request("OPTIONS", path, queryParams=queryParams)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


# Class action helpers
def cs_class_send_invitations(class_id: str, student_ids: list[str], is_multiple: bool = True) -> dict:
    """Send invitations to students in a class"""
    return cs_request("POST", "/class/actions/sendinvitations",
                      queryParams={"isMultiple": str(is_multiple).lower()},
                      content={"classId": class_id, "studentIds": student_ids})


def cs_class_suspend_all_environments(class_id: str) -> dict:
    """Suspend all environments in a class"""
    return cs_request("PUT", "/class/actions/suspendallenvironments",
                      content={"id": class_id})


def cs_class_delete_all_environments(class_id: str) -> dict:
    """Delete all environments in a class"""
    return cs_request("DELETE", "/class/actions/deleteallenvironments",
                      content={"id": class_id})


def cs_class_create_sponsored_link(class_id: str, student_email: str,
                                   student_first_name: str | None = None,
                                   student_last_name: str | None = None,
                                   pre_register: bool = False,
                                   registration_info: dict | None = None) -> dict:
    """Create a sponsored link for a student"""
    payload = {
        "classId": class_id,
        "studentEmail": student_email,
        "preRegisterStudent": pre_register,
    }
    if student_first_name is not None:
        payload["studentFirstName"] = student_first_name
    if student_last_name is not None:
        payload["studentLastName"] = student_last_name
    if registration_info is not None:
        payload["registrationInfo"] = registration_info
    return cs_post("/class/sponsoredlink", payload)


def cs_class_disable_sponsored_link(class_id: str, student_email: str,
                                    unregister_student: bool = False) -> dict:
    """Disable a sponsored link for a student"""
    return cs_post("/class/disablesponsoredlink", {
        "classId": class_id,
        "studentEmail": student_email,
        "unregisterStudent": unregister_student,
    })


def cs_class_resume_student_environment(class_id: str, student_ids: list[str]) -> dict:
    """Resume environment for a student in a class"""
    return cs_post(f"/Class/{class_id}/Students/actions/ResumeEnvironmentForStudent", {
        "classId": class_id,
        "studentIds": student_ids,
    })


def cs_class_get_detailed(class_id: str) -> dict:
    """Get detailed class information"""
    return cs_get("/Class/actions/getdetailed", {"classId": class_id})


def cs_class_get_countries() -> dict:
    """Get list of countries for class registration"""
    return cs_get("/class/actions/countries")


def cs_class_get_custom_fields() -> dict:
    """Get custom fields for class registration"""
    return cs_get("/class/actions/customfields")


# Student CRUD helpers
def cs_class_student_get_all(class_id: str) -> list[dict]:
    """Get all students in a class"""
    return cs_get(f"/class/{class_id}/students")


def cs_class_student_get(class_id: str, student_id: str) -> dict:
    """Get a specific student by ID"""
    return cs_get(f"/class/{class_id}/students/{student_id}")


def cs_class_student_create(class_id: str, email: str,
                            first_name: str | None = None,
                            last_name: str | None = None) -> dict:
    """Create a student in a class"""
    payload = {"email": email}
    if first_name is not None:
        payload["firstName"] = first_name
    if last_name is not None:
        payload["LastName"] = last_name
    return cs_post(f"/class/{class_id}/students", payload)


def cs_class_student_update(class_id: str, student_id: str, payload: dict) -> dict:
    """Update a student in a class"""
    return cs_request("PUT", f"/class/{class_id}/students/{student_id}",
                      content=payload)


def cs_class_student_delete(class_id: str, student_id: str) -> dict:
    """Delete a student from a class"""
    return cs_delete(f"/class/{class_id}/students/{student_id}")


# Instructor helpers
def cs_instructor_create(instructor_vup_id: str, class_id: str,
                         send_invite_now: bool = True,
                         disable_env_creation: bool = True) -> dict:
    """Create an instructor for a class"""
    return cs_post("/instructors", {
        "instructorVupId": instructor_vup_id,
        "classId": class_id,
        "sendInviteNow": send_invite_now,
        "disableEnvCreation": disable_env_creation,
    })


def cs_instructor_delete(instructor_id: str) -> dict:
    """Delete an instructor"""
    return cs_delete(f"/instructors/{instructor_id}")


def cs_instructor_get_by_class(class_id: str | None = None) -> list[dict]:
    """Get instructors, optionally filtered by class"""
    params = {"classId": class_id} if class_id is not None else None
    return cs_get("/instructors/class", params)


# ──────────────────────────────────────────
# Webhook helpers
# ──────────────────────────────────────────


def cs_webhook_get_all() -> list[dict]:
    """Get all webhooks"""
    return cs_get("/webhooks")


def cs_webhook_get(webhook_id: str) -> dict:
    """Get webhook details by ID"""
    return cs_get(f"/webhooks/{webhook_id}")


def cs_webhook_create(url: str, event: str) -> dict:
    """Create a webhook"""
    return cs_post("/webhooks", {"url": url, "event": event})


def cs_webhook_delete(webhook_id: str) -> dict:
    """Delete a webhook"""
    return cs_delete(f"/webhooks/{webhook_id}")


# ──────────────────────────────────────────
# Permalink helpers
# ──────────────────────────────────────────


def cs_permalink_create(snapshot_id: str) -> dict:
    """Create a permalink for a snapshot"""
    return cs_post("/permalinks", {"snapshotId": snapshot_id})


def cs_permalink_get(permalink_id: str) -> dict:
    """Get permalink details by ID"""
    return cs_get("/permalinks", {"permalinkId": permalink_id})


# ──────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────


def cs_ping() -> dict:
    """Ping the CloudShare API"""
    return cs_get("/ping")


def cs_region_get_all() -> list[dict]:
    """Get all regions"""
    return cs_get("/regions")


def cs_timezone_get_all() -> list[dict]:
    """Get all timezones"""
    return cs_get("/timezones")


# ──────────────────────────────────────────
# Team helpers
# ──────────────────────────────────────────


def cs_team_get_all() -> list[dict]:
    """Get all teams"""
    return cs_get("/teams")


def cs_team_create(name: str) -> dict:
    """Create a team"""
    return cs_post("/teams", {"name": name})


# ──────────────────────────────────────────
# Invitation helpers
# ──────────────────────────────────────────


def cs_invite_project_member(email: str, project_id: str, role: str) -> dict:
    """Invite a project member"""
    return cs_post("/invitations/actions/inviteprojectmember", {
        "email": email,
        "projectId": project_id,
        "role": role,
    })


def cs_invite_to_poc(email: str, topology_id: str) -> dict:
    """Invite to a POC"""
    return cs_post("/invitations/actions/invitetopoc", {
        "email": email,
        "topologyId": topology_id,
    })


def cs_get_login_url() -> dict:
    """Get login URL"""
    return cs_get("/users/actions/getloginurl")


# ──────────────────────────────────────────
# Analytics helpers
# ──────────────────────────────────────────


def cs_class_guided_journey_progress(class_id: str) -> dict:
    """Get guided journey progress for a class"""
    return cs_get(f"/classAnalytics/guided-journey/class/progress/{class_id}")


def cs_student_guided_journey_progress(student_id: str) -> dict:
    """Get guided journey progress for a student"""
    return cs_get(f"/classAnalytics/guided-journey/student/progress/{student_id}")


def cs_shared_environment_get(project_id: str, base_blueprint_id: str,
                              region_id: str, class_id: str) -> list[dict]:
    """Get shared environments"""
    return cs_get("/sharedenv", {
        "projectId": project_id,
        "baseBlueprintId": base_blueprint_id,
        "regionId": region_id,
        "classId": class_id,
    })


def cs_public_cloud_get(environment_id: str) -> dict:
    """Get public cloud details for an environment"""
    return cs_get(f"/externalclouds/ervins/{environment_id}")
