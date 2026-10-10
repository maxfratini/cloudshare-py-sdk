import os
import unittest

from mxcloudshare.cloudshare import req
from mxcloudshare.mxcloudshare import (
    cs_blueprint_get_all,
    cs_class_get_all,
    cs_env_create,
    cs_env_delete,
    cs_env_get_all,
    cs_env_resume,
    cs_env_suspend,
    cs_policy_get_all,
    cs_set_auth_keys,
    cs_snapshot_get_for_env,
    cs_snapshot_take,
)

REAL_KEYS_AVAILABLE = "CLOUDSHARE_API_ID" in os.environ and "CLOUDSHARE_API_KEY" in os.environ


def _authed_helpers():
    """Set auth keys from env vars and return them."""
    api_id = os.environ["CLOUDSHARE_API_ID"]
    api_key = os.environ["CLOUDSHARE_API_KEY"]
    cs_set_auth_keys(api_id, api_key)
    return api_id, api_key


def _target_env_id(testcase, var="CLOUDSHARE_TEST_ENV_ID"):
    """Env ID that mutating tests may touch; skip unless explicitly designated.

    Never pick an environment from the account listing: the account may hold real ones.
    """
    env_id = os.environ.get(var)
    if not env_id:
        testcase.skipTest(f"Mutating test: set {var} to a disposable environment ID to enable")
    return env_id


class TestIntegration(unittest.TestCase):

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_get_projects(self):
        """Raw req helper: GET /projects -- requires sandbox creds in CI."""
        api_id = os.environ["CLOUDSHARE_API_ID"]
        api_key = os.environ["CLOUDSHARE_API_KEY"]
        res = req(hostname="use.cloudshare.com",
                  method="GET",
                  apiId=api_id,
                  apiKey=api_key,
                  path="projects")
        self.assertEqual(2, res.status // 100)

    # ------------------------------------------------------------------ #
    # Environment lifecycle: suspend / resume / delete                   #
    # ------------------------------------------------------------------ #

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_list(self):
        """cs_env_get_all returns a list of environments -- requires sandbox creds in CI."""
        _authed_helpers()
        envs = cs_env_get_all()
        self.assertIsInstance(envs, list)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_suspend(self):
        """cs_env_suspend accepts an env ID and returns a dict -- requires sandbox creds in CI."""
        _authed_helpers()
        env_id = _target_env_id(self)
        result = cs_env_suspend(env_id)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_resume(self):
        """cs_env_resume accepts an env ID and returns a dict -- requires sandbox creds in CI."""
        _authed_helpers()
        env_id = _target_env_id(self)
        result = cs_env_resume(env_id)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_delete(self):
        """cs_env_delete on the env in CLOUDSHARE_TEST_DELETE_ENV_ID (destroys it!) -- opt-in only."""
        _authed_helpers()
        env_id = _target_env_id(self, "CLOUDSHARE_TEST_DELETE_ENV_ID")
        result = cs_env_delete(env_id)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_create_then_delete(self):
        """cs_env_create builds a real env, which is deleted right after.

        Opt-in: needs CLOUDSHARE_TEST_{BLUEPRINT,PROJECT,REGION,POLICY}_ID (use a 0-VM blueprint).
        """
        ids = {k: os.environ.get(f"CLOUDSHARE_TEST_{k}_ID") for k in ("BLUEPRINT", "PROJECT", "REGION", "POLICY")}
        missing = [k for k, v in ids.items() if not v]
        if missing:
            self.skipTest(f"Creating test: set CLOUDSHARE_TEST_{{{','.join(missing)}}}_ID to enable")
        _authed_helpers()
        created = cs_env_create(ids["BLUEPRINT"], ids["POLICY"], "mxcloudshare-it-create", "integration test - safe to delete",
                                project_id=ids["PROJECT"], region_id=ids["REGION"])
        env_id = created["environmentId"]
        self.addCleanup(cs_env_delete, env_id)
        self.assertTrue(env_id.startswith("EN"))

    # ------------------------------------------------------------------ #
    # Snapshot list / take                                                #
    # ------------------------------------------------------------------ #

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_snapshot_list(self):
        """cs_snapshot_get_for_env returns snapshots for an env -- requires sandbox creds in CI."""
        _authed_helpers()
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to list snapshots for")
        env_id = envs[0]["id"]
        snapshots = cs_snapshot_get_for_env(env_id)
        self.assertIsInstance(snapshots, list)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_snapshot_take(self):
        """cs_snapshot_take returns a dict -- requires sandbox creds in CI."""
        _authed_helpers()
        env_id = _target_env_id(self)
        try:
            result = cs_snapshot_take(env_id, name="integration-test-snapshot")
        except Exception as exc:
            if str(exc).startswith("403"):
                self.skipTest(f"Account lacks snapshot permission on the test environment: {exc}")
            raise
        self.assertIsInstance(result, dict)

    # ------------------------------------------------------------------ #
    # Class listing                                                        #
    # ------------------------------------------------------------------ #

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_class_list(self):
        """cs_class_get_all returns a list of classes -- requires sandbox creds in CI."""
        _authed_helpers()
        classes = cs_class_get_all()
        self.assertIsInstance(classes, list)

    # ------------------------------------------------------------------ #
    # Blueprint listing                                                    #
    # ------------------------------------------------------------------ #

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_blueprint_list(self):
        """cs_blueprint_get_all returns a list of blueprints -- requires sandbox creds in CI."""
        _authed_helpers()
        blueprints = cs_blueprint_get_all()
        self.assertIsInstance(blueprints, list)

    # ------------------------------------------------------------------ #
    # Policy listing                                                       #
    # ------------------------------------------------------------------ #

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_policy_list(self):
        """cs_policy_get_all returns a list of policies -- requires sandbox creds in CI."""
        _authed_helpers()
        policies = cs_policy_get_all()
        self.assertIsInstance(policies, list)