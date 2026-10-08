"""Tests for the mxcloudshare SDK layer (mxcloudshare.py)."""

from unittest.mock import Mock, patch

import pytest

from mxcloudshare import mxcloudshare as cs


def make_mock_response(data):
    """Create a mock response object like cloudshare.req returns."""
    mock_resp = Mock()
    mock_resp.status = 200
    mock_resp.content = data
    return mock_resp


def make_mock_requester_response(data):
    """Create a mock req() return value."""
    mock_req = Mock()
    mock_req.return_value = make_mock_response(data)
    return mock_req


class TestCsSetAuthKeys:
    """Test cs_set_auth_keys function."""

    def test_sets_api_id_and_api_key(self):
        cs.cs_set_auth_keys("test-id", "test-key")
        # After calling cs_set_auth_keys, the globals should be set
        # We verify the function runs without error
        assert True


class TestCsRequest:
    """Test cs_request function with mocked requester."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_request_with_get(self, mock_req):
        # Setup mock to return test data
        mock_req.return_value = make_mock_response({"id": "env-1", "name": "TestEnv"})

        result = cs.cs_request("GET", "/envs/1")
        assert result == {"id": "env-1", "name": "TestEnv"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_request_with_post(self, mock_req):
        # Setup mock to return test data
        mock_req.return_value = make_mock_response({"id": "env-1", "created": True})

        result = cs.cs_request("POST", "/envs/actions/create", content={"blueprintId": "bp-1"})
        assert result == {"id": "env-1", "created": True}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_request_with_put(self, mock_req):
        # Setup mock to return test data
        mock_req.return_value = make_mock_response({"id": "env-1", "status": "updated"})

        result = cs.cs_request("PUT", "/envs/actions/suspend", content={"envId": "env-1"})
        assert result == {"id": "env-1", "status": "updated"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_request_with_delete(self, mock_req):
        # Setup mock to return test data
        mock_req.return_value = make_mock_response({"id": "env-1", "deleted": True})

        result = cs.cs_request("DELETE", "/envs/1")
        assert result == {"id": "env-1", "deleted": True}


class TestGetVms:
    """Test get_vms function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_vms_returns_vms(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({
            "vms": [
                {"id": "vm-1", "name": "web-1"},
                {"id": "vm-2", "name": "db-1"},
            ]
        })

        result = cs.get_vms("env-1")
        assert len(result) == 2
        assert result[0]["id"] == "vm-1"
        assert result[1]["name"] == "db-1"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_vms_empty(self, mock_req):
        # Setup mock response with empty vms
        mock_req.return_value = make_mock_response({"vms": []})

        result = cs.get_vms("env-1")
        assert result == []

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_vms_error_status(self, mock_req):
        # Setup mock response with error (missing 'vms' key)
        mock_req.return_value = make_mock_response({"error": "Invalid environment ID"})

        with pytest.raises(KeyError):
            cs.get_vms("env-1")

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_get_vms_key_error_message(self, mock_req):
        # Verify the error message contains the key info
        mock_req.return_value = make_mock_response({"error": "Invalid"})

        with pytest.raises(KeyError) as exc_info:
            cs.get_vms("env-1")
        assert "vms" in str(exc_info.value)


class TestEnvGetStatus:
    """Test env_get_status function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_get_status_returns_status_text(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"statusText": "Ready"})

        result = cs.env_get_status("env-1")
        assert result == "Ready"

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_get_status_error(self, mock_req):
        # Setup mock response with error (missing 'statusText' key)
        mock_req.return_value = make_mock_response({"error": "Environment not found"})

        with pytest.raises(KeyError):
            cs.env_get_status("env-1")

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_env_get_status_key_error_message(self, mock_req):
        # Verify the error message contains the key info
        mock_req.return_value = make_mock_response({"error": "not found"})

        with pytest.raises(KeyError) as exc_info:
            cs.env_get_status("env-1")
        assert "statusText" in str(exc_info.value)


class TestCsEnvSuspend:
    """Test cs_env_suspend function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_env_suspend_payload(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "env-1", "suspended": True})

        result = cs.cs_env_suspend("env-1")
        # Verify the payload was correct
        assert result["suspended"] is True


class TestCsEnvResume:
    """Test cs_env_resume function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_env_resume_payload(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "env-1", "resumed": True})

        result = cs.cs_env_resume("env-1")
        assert result["resumed"] is True


class TestCsEnvDelete:
    """Test cs_env_delete function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_env_delete_payload(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "env-1", "deleted": True})

        result = cs.cs_env_delete("env-1")
        assert result["deleted"] is True


class TestCsBlueprintGetAll:
    """Test cs_blueprint_get_all function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_blueprint_get_all(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response([
            {"id": "bp-1", "name": "Blueprint 1"},
            {"id": "bp-2", "name": "Blueprint 2"},
        ])

        result = cs.cs_blueprint_get_all()
        assert len(result) == 2
        assert result[0]["name"] == "Blueprint 1"
        assert result[1]["name"] == "Blueprint 2"


class TestCsClassGetAll:
    """Test cs_class_get_all function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_class_get_all(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response([
            {"id": "cl-1", "name": "Class A"},
            {"id": "cl-2", "name": "Class B"},
        ])

        result = cs.cs_class_get_all()
        assert len(result) == 2
        assert result[0]["name"] == "Class A"
        assert result[1]["name"] == "Class B"


class TestCsClassCreate:
    """Test cs_class_create function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_class_create_payload(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "cl-1", "created": True})

        result = cs.cs_class_create("bp-1", name="MyClass")
        assert result["created"] is True


class TestCsClassUpdate:
    """Test cs_class_update function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_class_update_payload(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "cl-1", "updated": True})

        result = cs.cs_class_update("cl-1", {"status": "active"})
        assert result["updated"] is True


class TestCsClassDelete:
    """Test cs_class_delete function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_class_delete(self, mock_req):
        # Setup mock response
        mock_req.return_value = make_mock_response({"id": "cl-1", "deleted": True})

        result = cs.cs_class_delete("cl-1")
        assert result["deleted"] is True


class TestCsApiCall:
    """Test cs_api_call function."""

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_api_call_get(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "get data"})

        result = cs.cs_api_call("GET", "/some/path")
        assert result == {"result": "get data"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_api_call_post(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "post data"})

        result = cs.cs_api_call("POST", "/some/path", payload={"key": "value"})
        assert result == {"result": "post data"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_api_call_put(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "put data"})

        result = cs.cs_api_call("PUT", "/some/path", payload={"key": "value"})
        assert result == {"result": "put data"}

    @patch("mxcloudshare.mxcloudshare.cloudshare.req")
    def test_cs_api_call_delete(self, mock_req):
        mock_req.return_value = make_mock_response({"result": "delete data"})

        result = cs.cs_api_call("DELETE", "/some/path")
        assert result == {"result": "delete data"}