import os
import unittest

from mxcloudshare.cloudshare import req
from mxcloudshare.mxcloudshare import (
    cs_blueprint_get_all,
    cs_class_get_all,
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
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to suspend")
        env_id = envs[0]["id"]
        result = cs_env_suspend(env_id)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_resume(self):
        """cs_env_resume accepts an env ID and returns a dict -- requires sandbox creds in CI."""
        _authed_helpers()
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to resume")
        env_id = envs[0]["id"]
        result = cs_env_resume(env_id)
        self.assertIsInstance(result, dict)

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_env_delete(self):
        """cs_env_delete accepts an env ID and returns a dict -- requires sandbox creds in CI."""
        _authed_helpers()
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to delete")
        env_id = envs[0]["id"]
        result = cs_env_delete(env_id)
        self.assertIsInstance(result, dict)

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
        envs = cs_env_get_all()
        if not envs:
            self.skipTest("No environments available to take snapshot of")
        env_id = envs[0]["id"]
        result = cs_snapshot_take(env_id, name="integration-test-snapshot")
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