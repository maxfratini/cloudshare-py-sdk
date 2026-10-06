import unittest
from unittest.mock import Mock

from mxcloudshare.cloudshare.requester import Requester


def make_requester(auth_value="AUTH_PARAM"):
    http = Mock()
    http.request = Mock(return_value=Mock(status=200, content=""))
    authParamProvider = Mock()
    authParamProvider.get = Mock(return_value=auth_value)
    return Requester(http, authParamProvider), http, authParamProvider


class TestRequester(unittest.TestCase):

    def test_cs_request_passes_the_url_without_path_and_without_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY")

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/", url)

    def test_cs_request_passes_the_url_with_path_and_without_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path="some/path")

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/some/path", url)

    def test_cs_request_passes_the_url_with_path_prefixed_and_without_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path="/some/path")

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/some/path", url)

    def test_cs_request_passes_the_url_with_path_suffixed_and_without_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path="some/path/")

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/some/path", url)

    def test_cs_request_passes_the_url_with_path_with_spaces_slashes_and_without_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path=" /some/path/ ")

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/some/path", url)

    def test_cs_request_passes_the_url_with_path_and_with_query_string(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path="some/path",
                             queryParams={"foo": "bar", "aaa": 123})

        url = http.request.call_args[0][1]
        self.assertEqual("https://some.hostname.com/api/v3/some/path?foo=bar&aaa=123", url)

    def test_cs_request_passes_all_required_headers(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY")

        headers = http.request.call_args[0][2]
        self.assertEqual({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "cs_sha1 AUTH_PARAM",
        }, headers)

    def test_cs_request_passes_apiId_apiKey_and_url_to_authenticationParameterProvider(self):
        requester, _, authParamProvider = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="GET",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             path="envs")

        kwargs = authParamProvider.get.call_args[1]
        self.assertEqual("https://some.hostname.com/api/v3/envs", kwargs["url"])

    def test_cs_request_passes_a_json_string_content_to_http_request(self):
        requester, http, _ = make_requester()

        requester.cs_request(hostname="some.hostname.com",
                             method="POST",
                             apiId="API_ID",
                             apiKey="API_KEY",
                             content={"foo": {"aaa": 123}, "bar": "chicka"})

        content = http.request.call_args[0][3]
        self.assertEqual('{"foo": {"aaa": 123}, "bar": "chicka"}', content)

    def test_cs_request_returns_the_http_status_and_parsed_content(self):
        requester, http, _ = make_requester()
        http.request.return_value = Mock(status=201, content='{"id": "abc"}')

        res = requester.cs_request(hostname="some.hostname.com",
                                   method="GET",
                                   apiId="API_ID",
                                   apiKey="API_KEY")

        self.assertEqual(201, res.status)
        self.assertEqual({"id": "abc"}, res.content)

    def test_cs_request_returns_none_content_when_body_is_not_json(self):
        requester, http, _ = make_requester()
        http.request.return_value = Mock(status=500, content="not json")

        res = requester.cs_request(hostname="some.hostname.com",
                                   method="GET",
                                   apiId="API_ID",
                                   apiKey="API_KEY")

        self.assertEqual(500, res.status)
        self.assertIsNone(res.content)