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


def req(hostname, method, apiId, apiKey, path="", queryParams=None, content=None):
    return _get_requester().cs_request(hostname=hostname,
                                       method=method,
                                       apiId=apiId,
                                       apiKey=apiKey,
                                       path=path,
                                       queryParams=queryParams,
                                       content=content)


def _get_requester():
    from .ioc import get_requester
    return get_requester()
