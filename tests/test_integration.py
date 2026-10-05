import os
import unittest

from mxcloudshare.cloudshare import req

REAL_KEYS_AVAILABLE = "CLOUDSHARE_API_ID" in os.environ and "CLOUDSHARE_API_KEY" in os.environ


class TestIntegration(unittest.TestCase):

    @unittest.skipUnless(REAL_KEYS_AVAILABLE,
                         "This test only runs if CLOUDSHARE_API_{ID,KEY} envars are defined.")
    def test_get_projects(self):
        api_id = os.environ["CLOUDSHARE_API_ID"]
        api_key = os.environ["CLOUDSHARE_API_KEY"]
        res = req(hostname="use.cloudshare.com",
                  method="GET",
                  apiId=api_id,
                  apiKey=api_key,
                  path="projects")
        self.assertEqual(2, res.status // 100)