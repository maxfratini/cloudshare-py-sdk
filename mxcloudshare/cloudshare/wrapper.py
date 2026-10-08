#!/usr/bin/python
import copy
import os
import re

from .ioc import get_requester


def memoize(f):
    memo = {}

    def helper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]

    return helper


@memoize
def get_obj_id(url, obj_name):
    for obj in get(url):
        if obj['name'] == obj_name:
            return obj['id']
    else:
        raise Exception(f'{obj_name} not found in {url}')


def get_obj_ids_by_pat(url, obj_name_pat):
    res = []

    for obj in get(url):
        if re.search(obj_name_pat, obj['name']):
            res.append(obj['id'])

    return res


def get_env_ids_by_pat(name_pat):
    return get_obj_ids_by_pat('/envs/?criteria=0', name_pat)


def get_proj_id(name):
    return get_obj_id('/projects/', name)


def get_bp_id(proj_id, name):
    return get_obj_id(f'/projects/{proj_id}/blueprints', name)


def get_snapshot_id(project_name, bp_name, snapshot_name):
    snap = get_bp_snapshot(project_name, bp_name, snapshot_name)
    return snap['id']


def get_policy_id(proj_id, name):
    return get_obj_id(f'/projects/{proj_id}/policies', name)


def get_region_id(name):
    return get_obj_id('/regions/', name)


def get_template_id(name, region_id):
    return get_obj_id(f'/templates?templateType=1&regionId={region_id}', name)


def create_env_from_bp_using_names(dct):
    '''
        expected dct:

        {
            "environment": {
                "name": "my env",
                "projectId": "my project",
                "policyId": "3 days",
                "regionId": 'Miami' / 'VMware_Singapore' / 'VMware_Amsterdam'
            },
            "itemsCart": [
                {
                    "type": 1,
                    "blueprintId": "my blueprint",
                    "snapshotId": "my snapshot"
                }
            ]
        }
    '''
    new_dct = copy.deepcopy(dct)

    new_dct['environment']['projectId'] = get_proj_id(new_dct['environment']['projectId'])
    new_dct['environment']['policyId'] = get_policy_id(new_dct['environment']['projectId'],
                                                   dct['environment']['policyId'])
    new_dct['environment']['regionId'] = get_region_id(new_dct['environment']['regionId'])

    new_dct['itemsCart'][0]['blueprintId'] = get_bp_id(new_dct['environment']['projectId'],
                                                       new_dct['itemsCart'][0]['blueprintId'])

    if new_dct['itemsCart'][0].get('snapshotId'):
        new_dct['itemsCart'][0]['snapshotId'] = get_snapshot_id(
                                                       new_dct['environment']['projectId'],
                                                       new_dct['itemsCart'][0]['blueprintId'],
                                                       new_dct['itemsCart'][0]['snapshotId'])

    return post('/envs', new_dct)


def create_env_from_tempalte_cart_using_names(dct):
    '''
    {
        expected dct:

       "environment":{
          "name": "John's environment",
          "projectId": "my project",
          "teamId": "my team",
          "policyId": "4 days",
          "regionId": 'Miami' / 'VMware_Singapore' / 'VMware_Amsterdam'
          "description": ""
       },
       "preview": false,
       "itemsCart": [
          {
             "type":2,
             "name": "my ubuntu",
             "description":"ubuntu running a webserver",
             "chocolateyPackages":[],
             "templateVmId":"Ubuntu 16.0"
          },
          {
             "type": 2,
             "name": "my windows",
             "description":" domain controller",
             "chocolateyPackages": [],
             "templateVmId": "Windows 2012"
          }
       ]
    }
    '''
    dct['environment']['projectId'] = get_proj_id(dct['environment']['projectId'])
    dct['environment']['policyId'] = get_policy_id(dct['environment']['projectId'],
                                                   dct['environment']['policyId'])
    dct['environment']['regionId'] = get_region_id(dct['environment']['regionId'])

    for item in dct['itemsCart']:
        item['name'] = item['templateVmId']
        item['description'] = item['templateVmId']
        item['templateVmId'] = get_template_id(item['templateVmId'],
                                               dct['environment']['regionId'])

    return post('/envs', dct)


def with_env_prefix(env_token):
    if not env_token.startswith('EN'):
        return 'EN' + env_token
    else:
        return env_token


def suspend(env_token):
    return put(f'/envs/actions/suspend?envId={with_env_prefix(env_token)}&immediate=true')


def resume(env_token):
    return put(f'/envs/actions/resume?envId={with_env_prefix(env_token)}')


def revert(env_token):
    return put(f'/envs/actions/revert?envId={with_env_prefix(env_token)}')


def env_get_extended(env_token):
    return get(f'/envs/actions/getextended?envId={with_env_prefix(env_token)}')


def env_get_short(env_token):
    return get(f'/envs/{with_env_prefix(env_token)}')


def get_envs():
    return get('envs/?brief=false')


def del_env(env_token):
    return request('DELETE', '/envs/' + with_env_prefix(env_token))


def get_project_bps(project_name):
    return get(f'/Projects/{get_proj_id(project_name)}/blueprints')


def remove_bp_from_project(project_name, bp_name):
    """Remove a blueprint from a project.

    If bp_name starts with 'BP' and contains no spaces, it is treated as
    a raw blueprint ID. Otherwise it is resolved by name within the project.
    """
    if bp_name.startswith('BP') and bp_name.find(' ') == -1:
        bp_id = bp_name
    else:
        bp_id = get_bp_id(get_proj_id(project_name), bp_name)
    return put(f'/Projects/{get_proj_id(project_name)}/blueprints/{bp_id}/removeFromProject')


def add_bp_to_project(src_project_name, dest_project_name, bp_name):
    return post(f'/Projects/{get_proj_id(dest_project_name)}/blueprints/{get_bp_id(get_proj_id(src_project_name), bp_name)}/Post')


def add_bp_id_to_project(dest_project_name, bp_id):
    """Add a blueprint to a project using a pre-resolved blueprint ID."""
    return post(f'/Projects/{get_proj_id(dest_project_name)}/blueprints/{bp_id}/Post')


def execute_path(vm_id, command):
    content = {
        "vmId": vm_id,
        "path": command
    }
    return post('/vms/actions/executepath', content)


def check_execution_status(vm_id, execution_id):
    return get(f'/vms/actions/checkexecutionstatus?vmId={vm_id}&executionId={execution_id}')


def take_snapshot(env_id, new_snapshot_name, set_as_default, new_bp_name=None):
    content = {
        "envId": env_id,
        "name": new_snapshot_name,
        "description": "This Snapshot's description",
        "newBlueprintName": new_bp_name,
        "otherBlueprintId": None,
        "setAsDefault": set_as_default
    }

    return post('/snapshots/actions/takesnapshot', content)


def get_bp(project_name, bp_name):
    project_id = get_proj_id(project_name)
    bp_id = get_bp_id(project_id, bp_name)
    return get(f'/projects/{project_id}/blueprints/{bp_id}')


def get_bp_by_id(bp_id):
    """Get blueprint details by ID (no project lookup needed)."""
    return get(f'/blueprints/{bp_id}')


def get_bp_snapshots(project_name, bp_name):
    bp = get_bp(project_name, bp_name)
    return bp['createFromVersions']


def get_bp_snapshot(project_name, bp_name, snapshot_name):
    bp = get_bp(project_name, bp_name)
    matches = list(filter(lambda x: x['name']==snapshot_name, bp['createFromVersions']))
    if len(matches)==0:
        raise Exception(f'snapshot not found {project_name} {bp_name} {snapshot_name}')
    else:
        return matches[0]


def change_bp_ownership(proj_name, bp_name, node_id):
    proj_id = get_proj_id(proj_name)
    bp_id = get_bp_id(proj_id, bp_name)
    return put(f'/backendadmin/Actions/changeBlueprintOwner?blueprintId={bp_id}&nodeId={node_id}')

def validate_vix(machine_token):
    return post(f'/vms/actions/validateVix?vmId={machine_token}')


# ──────────────────────────────────────────
# ID translation helpers (ported from wrapper_cls)
# ──────────────────────────────────────────

def get_external_id(internal_id, entity_type='EN'):
    """Translate an internal ID to an external ID."""
    return get(f'/admin/Actions/TranslateInternalIdToExternalId?internalId={internal_id}&entityType={entity_type}')


def get_internal_id(external_id):
    """Translate an external ID to an internal ID."""
    return get(f'/admin/Actions/TranslateExternalIdToInternalId?externalId={external_id}')


def get_vm_list(env_token):
    """Get VM list for an environment via the viewer API."""
    return get(f'/viewer/actions/vmList?envId={env_token}')


def delete_bp(proj_name, bp_name):
    """Delete a blueprint by name within a project."""
    proj_id = get_proj_id(proj_name)
    bp_id = get_bp_id(proj_id, bp_name)
    return request('DELETE', f'/blueprints/actions/Delete?blueprintId={bp_id}')



def post(path, content=None):
    return request('POST', path, content=content)


def get(path, queryParams=None):
    return request('GET', path, queryParams=queryParams)


def put(path, queryParams=None, content=None):
    return request('PUT', path, queryParams=queryParams, content=content)


def request(method, path, queryParams=None, content=None):
    res = get_requester().cs_request(hostname=os.environ.get('CLOUDSHARE_HOSTNAME', "use.cloudshare.com"),
                                     method=method,
                                     apiId=os.environ.get('CLOUDSHARE_API_ID'),
                                     apiKey=os.environ.get('CLOUDSHARE_API_KEY'),
                                     path=path,
                                     queryParams=queryParams,
                                     content=content)

    if res.status // 100 != 2:
        print(res.status, res.content)
        raise Exception('Error')

    return res.content
