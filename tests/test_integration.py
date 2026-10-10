"""Integration tests against the real CloudShare API (PLAN-001 P4-1).

Skipped unless CLOUDSHARE_API_ID / CLOUDSHARE_API_KEY are exported. Run with
``make integration``, which exports them from ``cloudshare.env``.

Safety model:
- Read-only tests run against whatever the account holds.
- Mutating tests (suspend/resume/snapshot) run ONLY against the environment named
  in CLOUDSHARE_TEST_ENV_ID. Never against "the first env in the list".
- The lifecycle test creates its OWN throwaway environment from
  CLOUDSHARE_TEST_BLUEPRINT_ID / _REGION_ID / _POLICY_ID, exercises it, and deletes it
  in a ``finally``. That is the only place a delete runs.
"""

import os
import time
import unittest

from mxcloudshare.cloudshare import req
from mxcloudshare.mxcloudshare import (
    cs_api_call,
    cs_blueprint_get_all,
    cs_class_get_all,
    cs_env_create,
    cs_env_delete,
    cs_env_get,
    cs_env_get_all,
    cs_env_resume,
    cs_env_suspend,
    cs_ping,
    cs_policy_get_all,
    cs_project_blueprints_get_all,
    cs_project_get_all,
    cs_project_policies_get_all,
    cs_region_get_all,
    cs_set_auth_keys,
    cs_snapshot_get_for_env,
    cs_snapshot_take,
    cs_timezone_get_all,
)

REAL_KEYS_AVAILABLE = "CLOUDSHARE_API_ID" in os.environ and "CLOUDSHARE_API_KEY" in os.environ
TEST_ENV_ID = os.environ.get("CLOUDSHARE_TEST_ENV_ID")
TEST_BLUEPRINT_ID = os.environ.get("CLOUDSHARE_TEST_BLUEPRINT_ID")
TEST_REGION_ID = os.environ.get("CLOUDSHARE_TEST_REGION_ID")
TEST_POLICY_ID = os.environ.get("CLOUDSHARE_TEST_POLICY_ID")

needs_keys = unittest.skipUnless(
    REAL_KEYS_AVAILABLE, "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined."
)
needs_test_env = unittest.skipUnless(
    REAL_KEYS_AVAILABLE and TEST_ENV_ID,
    "Mutating test: set CLOUDSHARE_TEST_ENV_ID to a disposable environment to enable.",
)
needs_lifecycle = unittest.skipUnless(
    REAL_KEYS_AVAILABLE and TEST_BLUEPRINT_ID and TEST_REGION_ID and TEST_POLICY_ID,
    "Creates and deletes a real environment: set CLOUDSHARE_TEST_{BLUEPRINT,REGION,POLICY}_ID.",
)


def _authed_helpers():
    """Set auth keys from env vars and return them."""
    api_id = os.environ["CLOUDSHARE_API_ID"]
    api_key = os.environ["CLOUDSHARE_API_KEY"]
    cs_set_auth_keys(api_id, api_key)
    return api_id, api_key


class TestIntegrationReadOnly(unittest.TestCase):
    """Read-only calls: safe on any account."""

    def setUp(self):
        _authed_helpers()

    @needs_keys
    def test_get_projects_raw(self):
        """Raw req helper: GET /projects."""
        api_id, api_key = _authed_helpers()
        res = req(hostname="use.cloudshare.com", method="GET", apiId=api_id, apiKey=api_key, path="projects")
        self.assertEqual(2, res.status // 100)

    @needs_keys
    def test_project_list(self):
        self.assertIsInstance(cs_project_get_all(), list)

    @needs_keys
    def test_project_scoped_blueprints_and_policies(self):
        projects = cs_project_get_all()
        if not projects:
            self.skipTest("No projects available")
        project_id = projects[0]["id"]
        self.assertIsInstance(cs_project_blueprints_get_all(project_id), list)
        self.assertIsInstance(cs_project_policies_get_all(project_id), list)

    @needs_keys
    def test_env_list(self):
        self.assertIsInstance(cs_env_get_all(), list)

    @needs_keys
    def test_snapshot_list(self):
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to list snapshots for")
        self.assertIsInstance(cs_snapshot_get_for_env(envs[0]["id"]), list)

    @needs_keys
    def test_class_list(self):
        self.assertIsInstance(cs_class_get_all(), list)

    @needs_keys
    def test_blueprint_list_legacy_path(self):
        """ISS-005: the undocumented /blueprints path must keep working."""
        self.assertIsInstance(cs_blueprint_get_all(), list)

    @needs_keys
    def test_policy_list_legacy_path(self):
        """ISS-005: the undocumented /policies path must keep working."""
        self.assertIsInstance(cs_policy_get_all(), list)

    @needs_keys
    def test_utilities(self):
        self.assertIsNotNone(cs_ping())
        self.assertIsInstance(cs_region_get_all(), list)
        self.assertIsInstance(cs_timezone_get_all(), list)

    @needs_keys
    def test_generic_api_call_get(self):
        self.assertIsInstance(cs_api_call("GET", "projects"), (list, dict))


class TestIntegrationMutating(unittest.TestCase):
    """State-changing calls, pinned to CLOUDSHARE_TEST_ENV_ID."""

    def setUp(self):
        _authed_helpers()

    @needs_test_env
    def test_env_suspend_resume(self):
        self.assertIsInstance(cs_env_suspend(TEST_ENV_ID), dict)
        self.assertIsInstance(cs_env_resume(TEST_ENV_ID), dict)

    @needs_test_env
    def test_snapshot_take(self):
        try:
            result = cs_snapshot_take(TEST_ENV_ID, name="integration-test-snapshot")
        except Exception as exc:
            if str(exc).startswith("403"):
                self.skipTest(f"Account may not take snapshots: {exc}")
            raise
        self.assertIsInstance(result, dict)


class TestIntegrationLifecycle(unittest.TestCase):
    """create -> suspend -> resume -> delete on a throwaway environment."""

    def setUp(self):
        _authed_helpers()

    @needs_lifecycle
    def test_env_create_suspend_resume_delete(self):
        created = cs_env_create(TEST_BLUEPRINT_ID, name=f"mxcs-integration-test-{int(time.time())}",
                                description="Temporary: mxCloudShare integration test",
                                region_id=TEST_REGION_ID, policy_id=TEST_POLICY_ID)
        env_id = created["environmentId"]
        try:
            self._wait_for_status(env_id, "ready")
            self.assertIsInstance(cs_env_suspend(env_id), dict)
            self.assertIsInstance(cs_env_resume(env_id), dict)
        finally:
            cs_env_delete(env_id)
        self.assertNotIn(env_id, [e["id"] for e in cs_env_get_all()])

    def _wait_for_status(self, env_id, wanted, timeout=300, delay=10):
        deadline = time.monotonic() + timeout
        status = None
        while time.monotonic() < deadline:
            env = cs_env_get(env_id)
            status = env.get("statusText") or env.get("status")
            if str(status).lower() == wanted:
                return
            time.sleep(delay)
        self.fail(f"Environment {env_id} not {wanted!r} after {timeout}s (last status: {status!r})")
