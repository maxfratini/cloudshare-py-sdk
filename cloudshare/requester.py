# Copyright 2015 CloudShare Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from .http import Response

logger = logging.getLogger(__name__)


class Requester(object):

    def __init__(self, http, authenticationParameterProvider):
        self.http = http
        self.authenticationParameterProvider = authenticationParameterProvider

    def cs_request(self, hostname, method, apiId, apiKey, path="", queryParams=None, content=None):
        url = self._build_url(hostname, path, queryParams)
        json_content = json.dumps(content) if content is not None else None
        headers = self._build_headers(apiId, apiKey, url)
        res = self.http.request(method, url, headers, json_content)
        logger.debug(f"request: {method} {url} {headers} {json_content}")
        return Response(status=res.status, content=self._try_to_parse_json(res.content))

    def _build_headers(self, apiId, apiKey, url):
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "cs_sha1 %s" % self.authenticationParameterProvider.get(apiId=apiId, apiKey=apiKey, url=url)}
        logger.debug(f"headers: {headers}")
        return headers

    def _build_url(self, hostname, path, queryParams):
        base = "https://%s/api/v3/%s" % (hostname, self._condition_path_string(path))
        if queryParams:
            outurl = "%s?%s" % (base, urllib.parse.urlencode(queryParams))
            logger.debug(f"url: {outurl}")
            return outurl
        else:
            logger.debug(f"url: {base}")
            return base

    def _condition_path_string(self, path):
        return "/".join(path.strip("/ ").split("/"))

    def _try_to_parse_json(self, string):
        try:
            return json.loads(string)
        except json.JSONDecodeError:
            return None