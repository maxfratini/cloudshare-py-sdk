"""Tests for pre-existing SDK helpers — method, path, query/body mapping."""

from unittest.mock import Mock, patch

import pytest

from mxcloudshare import mxcloudshare as cs


def make_mock_response(data):
    """Create a mock response object like cloudshare.req returns."""
    mock_resp = Mock()
    mock_resp.status = 200
    mock_resp.content = data
    return mock_resp


# ──────────────────────────────────────────
# HTTP verb helpers
# ──────────────────────────────────────────


class TestCsPost:
    """Test cs_post helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_content(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_post("/class", {"name": "test"})
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class"
        assert mock_req.call_args[1]["content"] == {"name": "test"}


class TestCsGet:
    """Test cs_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_get("/envs", {"brief": "true"})
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/envs"
        assert mock_req.call_args[1]["queryParams"] == {"brief": "true"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_without_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_get("/ping")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/ping"
        assert mock_req.call_args[1].get("queryParams") is None


class TestCsPut:
    """Test cs_put helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_put_with_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_put("/envs/actions/suspend", {"envId": "env-1"})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/suspend"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}


class TestCsDelete:
    """Test cs_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_query_params(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_delete("/envs/env-1", {"force": "true"})
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"
        assert mock_req.call_args[1]["queryParams"] == {"force": "true"}


# ──────────────────────────────────────────
# cs_request mapping
# ──────────────────────────────────────────


class TestCsRequestMapping:
    """Test cs_request method/path/queryParams/content forwarding."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_forwards_method_and_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1"})
        cs.cs_request("GET", "/envs/env-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_post_forwards_method_path_and_content(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1"})
        cs.cs_request("POST", "/envs/actions/create", content={"blueprintId": "bp-1"})
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/envs/actions/create"
        assert mock_req.call_args[1]["content"] == {"blueprintId": "bp-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_put_forwards_method_path_and_query(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_request("PUT", "/envs/actions/suspend", {"envId": "env-1"})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/suspend"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_delete_forwards_method_and_path(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "ok"})
        cs.cs_request("DELETE", "/envs/env-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_raises_on_non_2xx(self, mock_req):
        mock_resp = Mock()
        mock_resp.status = 400
        mock_resp.content = {"message": "Bad request"}
        mock_req.return_value = mock_resp
        with pytest.raises(Exception, match="400 Bad request"):
            cs.cs_request("GET", "/bad")


# ──────────────────────────────────────────
# Environment helpers
# ──────────────────────────────────────────


class TestCsEnvGet:
    """Test cs_env_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1"})
        result = cs.cs_env_get("env-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"
        assert result == {"id": "env-1"}


class TestCsEnvGetAll:
    """Test cs_env_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_brief_false_default(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "env-1"}])
        result = cs.cs_env_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "envs/?brief=false"
        assert result == [{"id": "env-1"}]

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_brief_true(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "env-1"}])
        cs.cs_env_get_all(brief=True)
        assert mock_req.call_args[1]["path"] == "envs/?brief=true"


class TestCsEnvResume:
    """Test cs_env_resume helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_put_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1", "resumed": True})
        result = cs.cs_env_resume("env-1")
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/envs/actions/resume"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}
        assert result["resumed"] is True


class TestCsEnvDelete:
    """Test cs_env_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1", "deleted": True})
        result = cs.cs_env_delete("env-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/envs/env-1"
        assert result["deleted"] is True


class TestCsEnvCreate:
    """Test cs_env_create helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_blueprint_id_only(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1"})
        cs.cs_env_create("bp-1")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/envs/actions/create"
        assert mock_req.call_args[1]["content"] == {"blueprintId": "bp-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_all_fields(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "env-1"})
        cs.cs_env_create("bp-1", policy_id="pol-1", name="MyEnv", description="Test env")
        assert mock_req.call_args[1]["content"] == {
            "blueprintId": "bp-1",
            "policyId": "pol-1",
            "name": "MyEnv",
            "description": "Test env",
        }


# ──────────────────────────────────────────
# Blueprint helpers
# ──────────────────────────────────────────


class TestCsBlueprintGet:
    """Test cs_blueprint_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "bp-1"})
        result = cs.cs_blueprint_get("bp-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/blueprints/bp-1"
        assert result == {"id": "bp-1"}


# ──────────────────────────────────────────
# Policy helpers
# ──────────────────────────────────────────


class TestCsPolicyGetAll:
    """Test cs_policy_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "pol-1"}])
        result = cs.cs_policy_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/policies"
        assert result == [{"id": "pol-1"}]


class TestCsPolicyGet:
    """Test cs_policy_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "pol-1"})
        result = cs.cs_policy_get("pol-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/policies/pol-1"
        assert result == {"id": "pol-1"}


# ──────────────────────────────────────────
# Class helpers
# ──────────────────────────────────────────


class TestCsClassGet:
    """Test cs_class_get helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "cl-1"})
        result = cs.cs_class_get("cl-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class/cl-1"
        assert result == {"id": "cl-1"}


class TestCsClassGetAll:
    """Test cs_class_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get(self, mock_req):
        mock_req.return_value = make_mock_response([{"id": "cl-1", "name": "Class A"}])
        result = cs.cs_class_get_all()
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "/class"
        assert len(result) == 1
        assert result[0]["name"] == "Class A"


class TestCsClassCreate:
    """Test cs_class_create helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_blueprint_id_only(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "cl-1"})
        result = cs.cs_class_create("bp-1")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/class"
        assert mock_req.call_args[1]["content"] == {"blueprintId": "bp-1"}
        assert result == {"id": "cl-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_all_fields(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "cl-1"})
        cs.cs_class_create("bp-1", policy_id="pol-1", name="MyClass", description="Test class")
        assert mock_req.call_args[1]["content"] == {
            "blueprintId": "bp-1",
            "policyId": "pol-1",
            "name": "MyClass",
            "description": "Test class",
        }


class TestCsClassUpdate:
    """Test cs_class_update helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_put_with_body(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "cl-1", "updated": True})
        result = cs.cs_class_update("cl-1", {"status": "active"})
        assert mock_req.call_args[1]["method"] == "PUT"
        assert mock_req.call_args[1]["path"] == "/class/cl-1"
        assert mock_req.call_args[1]["queryParams"] == {"status": "active"}
        assert result["updated"] is True


class TestCsClassDelete:
    """Test cs_class_delete helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_delete_with_id_in_path(self, mock_req):
        mock_req.return_value = make_mock_response({"id": "cl-1", "deleted": True})
        result = cs.cs_class_delete("cl-1")
        assert mock_req.call_args[1]["method"] == "DELETE"
        assert mock_req.call_args[1]["path"] == "/class/cl-1"
        assert result["deleted"] is True


# ──────────────────────────────────────────
# VM helpers
# ──────────────────────────────────────────


class TestCsVmGetAll:
    """Test cs_vm_get_all helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_env_id(self, mock_req):
        mock_req.return_value = make_mock_response({
            "vms": [{"id": "vm-1", "name": "web-1"}],
        })
        result = cs.cs_vm_get_all("env-1")
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "envs/actions/getextended"
        assert mock_req.call_args[1]["queryParams"] == {"envId": "env-1"}
        assert len(result) == 1
        assert result[0]["name"] == "web-1"


class TestCsVmExecutePath:
    """Test cs_vm_execute_path helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_vm_id_and_path(self, mock_req):
        mock_req.return_value = make_mock_response({"executionId": "exec-1"})
        result = cs.cs_vm_execute_path("vm-1", "/usr/bin/test")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/vms/actions/executePath"
        assert mock_req.call_args[1]["content"] == {"vmId": "vm-1", "path": "/usr/bin/test"}
        assert result == {"executionId": "exec-1"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_args(self, mock_req):
        mock_req.return_value = make_mock_response({"executionId": "exec-1"})
        cs.cs_vm_execute_path("vm-1", "/usr/bin/test", args="--verbose")
        assert mock_req.call_args[1]["content"] == {
            "vmId": "vm-1", "path": "/usr/bin/test", "args": "--verbose",
        }


# ──────────────────────────────────────────
# Legacy helpers
# ──────────────────────────────────────────


class TestExecutePath:
    """Test execute_path helper (legacy signature)."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_post_with_machine_id_and_command(self, mock_req):
        mock_req.return_value = make_mock_response({"executionId": "exec-1"})
        cs.execute_path({"id": "vm-1"}, "/usr/bin/test")
        assert mock_req.call_args[1]["method"] == "POST"
        assert mock_req.call_args[1]["path"] == "/vms/actions/executePath"
        assert mock_req.call_args[1]["content"] == {"vmId": "vm-1", "path": "/usr/bin/test"}


class TestGetExecutionStatus:
    """Test get_execution_status helper."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_sends_get_with_vm_id_and_execution_id(self, mock_req):
        mock_req.return_value = make_mock_response({"status": "completed"})
        cs.get_execution_status({"id": "vm-1"}, {"executionId": "exec-1"})
        assert mock_req.call_args[1]["method"] == "GET"
        assert mock_req.call_args[1]["path"] == "vms/actions/checkExecutionStatus"
        assert mock_req.call_args[1]["queryParams"] == {
            "vmId": "vm-1", "executionId": "exec-1",
        }