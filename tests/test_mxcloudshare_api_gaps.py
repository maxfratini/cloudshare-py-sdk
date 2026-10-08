"""Tests for cs_api_call upgrade — method routing, query params, backward compat."""

from unittest.mock import Mock, patch

import pytest

from mxcloudshare import mxcloudshare as cs


def make_mock_response(data):
    """Create a mock response object like cloudshare.req returns."""
    mock_resp = Mock()
    mock_resp.status = 200
    mock_resp.content = data
    return mock_resp


class TestCsApiCallRouting:
    """Test that cs_api_call routes each method string correctly."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_routes_to_get_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("GET", "/envs")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/envs"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_post_routes_to_post_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("POST", "/class", payload={"name": "test"})
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_put_routes_to_put_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("PUT", "/class/cl-1", payload={"status": "active"})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/class/cl-1"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_routes_to_delete_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("DELETE", "/envs/env-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_patch_routes_to_patch_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("PATCH", "/envs", payload={"status": "updated"})
        assert mock_req.call_args[1]["method"] == "PATCH"
        assert mock_req.call_args[1]["path"] == "/envs"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_options_routes_to_options_method(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("OPTIONS", "/some/path")
        assert mock_req.call_args[1]["method"] == "OPTIONS"
        assert mock_req.call_args[1]["path"] == "/some/path"


class TestCsApiCallQueryParams:
    """Test that queryParams are forwarded on GET/DELETE and allowed elsewhere."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_forwards_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("GET", "/envs", queryParams={"brief": "true"})
        assert mock_req.call_args[1]["queryParams"] == {"brief": "true"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_forwards_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("DELETE", "/vms/vm-1", queryParams={"force": "true"})
        assert mock_req.call_args[1]["queryParams"] == {"force": "true"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_post_allows_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("POST", "/class", payload={"name": "test"}, queryParams={"extra": "1"})
        assert mock_req.call_args[1]["queryParams"] == {"extra": "1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_put_allows_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("PUT", "/class/cl-1", payload={"status": "active"}, queryParams={"notify": "true"})
        assert mock_req.call_args[1]["queryParams"] == {"notify": "true"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_query_params_none_when_omitted(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("GET", "/envs")
        assert mock_req.call_args[1]["queryParams"] is None

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_query_params_none_when_omitted(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("DELETE", "/envs/env-1")
        assert mock_req.call_args[1]["queryParams"] is None


class TestCsApiCallPayload:
    """Test payload/content mapping for body-bearing methods."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_post_sends_payload_as_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        payload = {"name": "test"}
        cs.cs_api_call("POST", "/class", payload=payload)
        assert mock_req.call_args[1]["content"] == payload

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_put_sends_payload_as_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        payload = {"status": "active"}
        cs.cs_api_call("PUT", "/class/cl-1", payload=payload)
        assert mock_req.call_args[1]["content"] == payload

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_patch_sends_payload_as_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        payload = {"status": "updated"}
        cs.cs_api_call("PATCH", "/envs", payload=payload)
        assert mock_req.call_args[1]["content"] == payload

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_options_has_no_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("OPTIONS", "/some/path")
        assert mock_req.call_args[1]["content"] is None

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_has_no_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("GET", "/envs")
        assert mock_req.call_args[1]["content"] is None

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_has_no_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("DELETE", "/envs/env-1")
        assert mock_req.call_args[1]["content"] is None

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_patch_without_payload(self, mock_req):
        """PATCH with no payload sends content=None."""
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_api_call("PATCH", "/envs")
        assert mock_req.call_args[1]["content"] is None


class TestCsApiCallUnsupportedMethod:
    """Test ValueError for unsupported methods."""

    def test_head_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported HTTP method: HEAD"):
            cs.cs_api_call("HEAD", "/some/path")

    def test_trace_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported HTTP method: TRACE"):
            cs.cs_api_call("TRACE", "/some/path")


class TestCsApiCallBackwardCompat:
    """Test that existing call shapes (same positional args) still work."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_method_path_only(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        result = cs.cs_api_call("GET", "/some/path")
        assert result == {"result": "ok"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_post_with_positional_payload(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        result = cs.cs_api_call("POST", "/some/path", {"key": "value"})
        assert result == {"result": "ok"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_put_with_positional_payload(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        result = cs.cs_api_call("PUT", "/some/path", {"key": "value"})
        assert result == {"result": "ok"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_method_path_only(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        result = cs.cs_api_call("DELETE", "/some/path")
        assert result == {"result": "ok"}


class TestCsEnvExtend:
    """Test cs_env_extend helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_extend_sends_put_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_env_extend("env-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/extend"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}


class TestCsEnvRevert:
    """Test cs_env_revert helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_revert_sends_put_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_env_revert("env-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/revert"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_revert_with_snapshot_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_env_revert("env-1", snapshot_id="snap-1")
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1", "snapshotId": "snap-1"}


class TestCsEnvPostponeInactivity:
    """Test cs_env_postpone_inactivity helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_postpone_inactivity_sends_put_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_env_postpone_inactivity("env-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/postponeinactivity"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}


class TestCsSnapshotGet:
    """Test cs_snapshot_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_get_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_get("snap-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/snapshots/snap-1"


class TestCsSnapshotGetForEnv:
    """Test cs_snapshot_get_for_env helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_get_for_env_sends_get_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_get_for_env("env-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/snapshots/actions/getforenv"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}


class TestCsSnapshotTake:
    """Test cs_snapshot_take helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_take_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_take("env-1", "My Snapshot")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/snapshots/actions/takesnapshot"
        assert mock_req.call_args[1]["content"] == {
            "envId": "env-1",
            "name": "My Snapshot",
        }
        # setAsDefault is omitted so the server applies its default (true)

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_take_with_set_as_default_explicit_false(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_take("env-1", "My Snapshot", set_as_default=False)
        assert mock_req.call_args[1]["content"] == {
            "envId": "env-1",
            "name": "My Snapshot",
            "setAsDefault": False,
        }

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_take_with_set_as_default_explicit_true(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_take("env-1", "My Snapshot", set_as_default=True)
        assert mock_req.call_args[1]["content"] == {
            "envId": "env-1",
            "name": "My Snapshot",
            "setAsDefault": True,
        }

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_take_with_all_optional_fields(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_take(
            "env-1", "My Snapshot", set_as_default=True,
            description="Test snap", new_blueprint_name="New BP",
            other_blueprint_id="bp-2",
        )
        assert mock_req.call_args[1]["content"] == {
            "envId": "env-1",
            "name": "My Snapshot",
            "setAsDefault": True,
            "description": "Test snap",
            "newBlueprintName": "New BP",
            "otherBlueprintId": "bp-2",
        }


class TestCsSnapshotMarkDefault:
    """Test cs_snapshot_mark_default helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_snapshot_mark_default_sends_put_with_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_snapshot_mark_default("snap-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/snapshots/actions/markdefault"
        assert mock_req.call_args[1]["queryParams"] == {"id": "snap-1"}


class TestCsVmReboot:
    """Test cs_vm_reboot helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_reboot_sends_put_with_vm_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_reboot("vm-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/vms/actions/reboot"
        assert mock_req.call_args[1]["queryParams"] == {"vmId": "vm-1"}


class TestCsVmRevert:
    """Test cs_vm_revert helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_revert_sends_put_with_vm_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_revert("vm-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/vms/actions/revert"
        assert mock_req.call_args[1]["queryParams"] == {"vmId": "vm-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_revert_with_snapshot_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_revert("vm-1", snapshot_id="snap-1")
        assert mock_req.call_args[1]["queryParams"] == {"vmId": "vm-1", "snapshotId": "snap-1"}


class TestCsVmDelete:
    """Test cs_vm_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_delete_sends_delete_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_delete("vm-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/vms/vm-1"


class TestCsVmEditHardware:
    """Test cs_vm_edit_hardware helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_edit_hardware_sends_put_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_edit_hardware("vm-1", {"numCpus": 4, "memorySizeMBs": 8192})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/vms/actions/editvmhardware"
        assert mock_req.call_args[1]["content"] == {"vmId": "vm-1", "numCpus": 4, "memorySizeMBs": 8192}


class TestCsVmGetRemoteAccessFile:
    """Test cs_vm_get_remote_access_file helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_get_remote_access_file_sends_get_with_vm_id(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_get_remote_access_file("vm-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/vms/actions/getremoteaccessfile"
        assert mock_req.call_args[1]["queryParams"] == {"vmId": "vm-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_vm_get_remote_access_file_with_desktop_size(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_vm_get_remote_access_file("vm-1", desktop_width=1280, desktop_height=720)
        assert mock_req.call_args[1]["queryParams"] == {
            "vmId": "vm-1", "desktopWidth": 1280, "desktopHeight": 720,
        }


class TestCsProjectGetAll:
    """Test cs_project_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_project_get_all_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "proj-1"}])
        result = cs.cs_project_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/projects"
        assert result == [{"id": "proj-1"}]


class TestCsProjectBlueprintsGetAll:
    """Test cs_project_blueprints_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_project_blueprints_get_all_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "bp-1"}])
        cs.cs_project_blueprints_get_all("proj-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/projects/proj-1/blueprints"
        assert mock_req.call_args[1]["queryParams"] is None

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_project_blueprints_get_all_with_query_params(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "bp-1"}])
        cs.cs_project_blueprints_get_all("proj-1", region_id="us-east", default_snapshot="yes")
        assert mock_req.call_args[1]["queryParams"] == {"regionId": "us-east", "defaultSnapshot": "yes"}


class TestCsProjectPoliciesGetAll:
    """Test cs_project_policies_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_project_policies_get_all_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "pol-1"}])
        cs.cs_project_policies_get_all("proj-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/projects/proj-1/policies"


class TestCsClassSendInvitations:
    """Test cs_class_send_invitations helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_query_and_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_send_invitations("cl-1", ["s-1", "s-2"])
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class/actions/sendinvitations"
        assert mock_req.call_args[1]["queryParams"] == {"isMultiple": "true"}
        assert mock_req.call_args[1]["content"] == {"classId": "cl-1", "studentIds": ["s-1", "s-2"]}


class TestCsClassSuspendAllEnvironments:
    """Test cs_class_suspend_all_environments helper (D2 exception)."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_put_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_suspend_all_environments("cl-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/class/actions/suspendallenvironments"
        assert mock_req.call_args[1]["content"] == {"id": "cl-1"}
        assert "queryParams" not in mock_req.call_args[1] or mock_req.call_args[1].get("queryParams") is None


class TestCsClassDeleteAllEnvironments:
    """Test cs_class_delete_all_environments helper (D2 exception)."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_delete_all_environments("cl-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/class/actions/deleteallenvironments"
        assert mock_req.call_args[1]["content"] == {"id": "cl-1"}
        assert "queryParams" not in mock_req.call_args[1] or mock_req.call_args[1].get("queryParams") is None


class TestCsClassCreateSponsoredLink:
    """Test cs_class_create_sponsored_link helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_required_only(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_create_sponsored_link("cl-1", "student@example.com")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class/sponsoredlink"
        assert mock_req.call_args[1]["content"] == {
            "classId": "cl-1",
            "studentEmail": "student@example.com",
            "preRegisterStudent": False,
        }

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_all_fields(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_create_sponsored_link("cl-1", "s@e.com", student_first_name="Jane",
                                          student_last_name="Doe", pre_register=True,
                                          registration_info={"country": "US"})
        assert mock_req.call_args[1]["content"] == {
            "classId": "cl-1",
            "studentEmail": "s@e.com",
            "studentFirstName": "Jane",
            "studentLastName": "Doe",
            "preRegisterStudent": True,
            "registrationInfo": {"country": "US"},
        }


class TestCsClassDisableSponsoredLink:
    """Test cs_class_disable_sponsored_link helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_disable_sponsored_link("cl-1", "student@example.com", unregister_student=True)
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class/disablesponsoredlink"
        assert mock_req.call_args[1]["content"] == {
            "classId": "cl-1",
            "studentEmail": "student@example.com",
            "unregisterStudent": True,
        }


class TestCsClassResumeStudentEnvironment:
    """Test cs_class_resume_student_environment helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_path_and_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_resume_student_environment("cl-1", ["s-1"])
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/Class/cl-1/Students/actions/ResumeEnvironmentForStudent"
        assert mock_req.call_args[1]["content"] == {"classId": "cl-1", "studentIds": ["s-1"]}


class TestCsClassGetDetailed:
    """Test cs_class_get_detailed helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_query(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_get_detailed("cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/Class/actions/getdetailed"
        assert mock_req.call_args[1]["queryParams"] == {"classId": "cl-1"}


class TestCsClassGetCountries:
    """Test cs_class_get_countries helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_no_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_get_countries()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class/actions/countries"


class TestCsClassGetCustomFields:
    """Test cs_class_get_custom_fields helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_no_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_get_custom_fields()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class/actions/customfields"


class TestCsClassStudentGetAll:
    """Test cs_class_student_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_path(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "s-1"}])
        cs.cs_class_student_get_all("cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class/cl-1/students"


class TestCsClassStudentGet:
    """Test cs_class_student_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_path_params(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "s-1"})
        cs.cs_class_student_get("cl-1", "s-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class/cl-1/students/s-1"


class TestCsClassStudentCreate:
    """Test cs_class_student_create helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_email_only(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "s-1"})
        cs.cs_class_student_create("cl-1", "student@example.com")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class/cl-1/students"
        assert mock_req.call_args[1]["content"] == {"email": "student@example.com"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_all_fields(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "s-1"})
        cs.cs_class_student_create("cl-1", "s@e.com", first_name="Jane", last_name="Doe")
        assert mock_req.call_args[1]["content"] == {"email": "s@e.com", "firstName": "Jane", "LastName": "Doe"}


class TestCsClassStudentUpdate:
    """Test cs_class_student_update helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_put_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "s-1"})
        cs.cs_class_student_update("cl-1", "s-1", {"firstName": "Jane"})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/class/cl-1/students/s-1"
        assert mock_req.call_args[1]["content"] == {"firstName": "Jane"}


class TestCsClassStudentDelete:
    """Test cs_class_student_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_path_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_class_student_delete("cl-1", "s-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/class/cl-1/students/s-1"


class TestCsInstructorCreate:
    """Test cs_instructor_create helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "inst-1"})
        cs.cs_instructor_create("vup-1", "cl-1")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/instructors"
        assert mock_req.call_args[1]["content"] == {
            "instructorVupId": "vup-1",
            "classId": "cl-1",
            "sendInviteNow": True,
            "disableEnvCreation": True,
        }


class TestCsInstructorDelete:
    """Test cs_instructor_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_path(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_instructor_delete("inst-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/instructors/inst-1"


class TestCsInstructorGetByClass:
    """Test cs_instructor_get_by_class helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_query_when_class_id_given(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "inst-1"}])
        cs.cs_instructor_get_by_class("cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/instructors/class"
        assert mock_req.call_args[1]["queryParams"] == {"classId": "cl-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_without_query_when_no_class_id(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "inst-1"}])
        cs.cs_instructor_get_by_class()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/instructors/class"
        assert mock_req.call_args[1]["queryParams"] is None


# ──────────────────────────────────────────
# Webhook helpers
# ──────────────────────────────────────────


class TestCsWebhookGetAll:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "wh-1"}])
        result = cs.cs_webhook_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/webhooks"
        assert result == [{"id": "wh-1"}]


class TestCsWebhookGet:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "wh-1"})
        cs.cs_webhook_get("wh-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/webhooks/wh-1"


class TestCsWebhookCreate:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "wh-1"})
        cs.cs_webhook_create("https://example.com/hook", "env.create")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/webhooks"
        assert mock_req.call_args[1]["content"] == {"url": "https://example.com/hook", "event": "env.create"}


class TestCsWebhookDelete:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_webhook_delete("wh-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/webhooks/wh-1"


# ──────────────────────────────────────────
# Permalink helpers
# ──────────────────────────────────────────


class TestCsPermalinkCreate:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_snapshot_id(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "pl-1"})
        cs.cs_permalink_create("snap-1")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/permalinks"
        assert mock_req.call_args[1]["content"] == {"snapshotId": "snap-1"}


class TestCsPermalinkGet:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_permalink_id_query(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "pl-1"})
        cs.cs_permalink_get("pl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/permalinks"
        assert mock_req.call_args[1]["queryParams"] == {"permalinkId": "pl-1"}


# ──────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────


class TestCsPing:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response({"message": "pong"})
        result = cs.cs_ping()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/ping"
        assert result == {"message": "pong"}


class TestCsRegionGetAll:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "us-east"}])
        result = cs.cs_region_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/regions"
        assert result == [{"id": "us-east"}]


class TestCsTimezoneGetAll:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "UTC"}])
        result = cs.cs_timezone_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/timezones"
        assert result == [{"id": "UTC"}]


# ──────────────────────────────────────────
# Team helpers
# ──────────────────────────────────────────


class TestCsTeamGetAll:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "team-1"}])
        result = cs.cs_team_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/teams"
        assert result == [{"id": "team-1"}]


class TestCsTeamCreate:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_name(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "team-1"})
        cs.cs_team_create("My Team")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/teams"
        assert mock_req.call_args[1]["content"] == {"name": "My Team"}


# ──────────────────────────────────────────
# Invitation helpers
# ──────────────────────────────────────────


class TestCsInviteProjectMember:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_invite_project_member("user@example.com", "proj-1", "Owner")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/invitations/actions/inviteprojectmember"
        assert mock_req.call_args[1]["content"] == {
            "email": "user@example.com",
            "projectId": "proj-1",
            "role": "Owner",
        }


class TestCsInviteToPoc:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_invite_to_poc("user@example.com", "topo-1")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/invitations/actions/invitetopoc"
        assert mock_req.call_args[1]["content"] == {
            "email": "user@example.com",
            "topologyId": "topo-1",
        }


class TestCsGetLoginUrl:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response({"url": "https://login.cloudshare.com"})
        result = cs.cs_get_login_url()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/users/actions/getloginurl"
        assert result == {"url": "https://login.cloudshare.com"}


# ──────────────────────────────────────────
# Analytics helpers
# ──────────────────────────────────────────


class TestCsClassGuidedJourneyProgress:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_class_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"progress": 50})
        cs.cs_class_guided_journey_progress("cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/classAnalytics/guided-journey/class/progress/cl-1"


class TestCsStudentGuidedJourneyProgress:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_student_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"progress": 75})
        cs.cs_student_guided_journey_progress("s-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/classAnalytics/guided-journey/student/progress/s-1"


class TestCsSharedEnvironmentGet:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_query_params(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "env-1"}])
        cs.cs_shared_environment_get("proj-1", "bp-1", "us-east", "cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/sharedenv"
        assert mock_req.call_args[1]["queryParams"] == {
            "projectId": "proj-1",
            "baseBlueprintId": "bp-1",
            "regionId": "us-east",
            "classId": "cl-1",
        }


class TestCsPublicCloudGet:
    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_env_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"provider": "aws"})
        cs.cs_public_cloud_get("env-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/externalclouds/ervins/env-1"