"""Tests for mxcloudshare.cloudshare.http."""

from unittest.mock import MagicMock, patch

from mxcloudshare.cloudshare.http import Http


class TestHttpTimeout:
    @patch("mxcloudshare.cloudshare.http.urllib.request.urlopen")
    def test_urlopen_is_called_with_a_timeout(self, mock_urlopen):
        resp = MagicMock()
        resp.getcode.return_value = 200
        resp.read.return_value = b"{}"
        mock_urlopen.return_value = resp

        Http().request("GET", "https://example.test/api/v3/envs", {}, None)

        assert mock_urlopen.call_args[1]["timeout"] == Http.TIMEOUT_SECS
