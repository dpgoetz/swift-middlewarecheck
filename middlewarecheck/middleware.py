# Copyright (c) 2010-2013 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ConfigParser import ConfigParser
import json
import os

from swift.common.swob import Request, Response


class MiddlewareCheckMiddleware(object):
    """
    Middlewarecheck middleware used for development/testing.

    If the path is /middlewarecheck, it will respond 200 with a JSON encoded
    list of middleware installed.

    Example:
    {
        "swift_proxy": {
            "pipeline": [
                "healthcheck",
                "middlewarecheck",
                "cache",
                "tempauth",
                "proxy-logging",
                "proxy-server"
            ]
        }
    }

    If the optional config parameter "disable_path" is set, and a file is
    present at that path, it will respond 503 with "DISABLED BY FILE" as the
    body.
    """

    def __init__(self, app, conf):
        self.app = app
        try:
            proxy_conf = ConfigParser()
            swift_dir = conf.get('swift_dir', '/etc/swift')
            proxy_conf.read(
                '{swift_dir}/proxy-server.conf'.format(swift_dir=swift_dir))
            self.pipeline = proxy_conf.get(
                'pipeline:main', 'pipeline').split(' ')
        except IOError:
            self.pipeline = None

        self.disable_path = conf.get('disable_path', '')

    def GET(self, req):
        """Returns a 200 response with the installed middleware in the body."""

        if not self.pipeline:
            return Response(
                request=req, body='Service Unavailable', status=503)

        body = json.dumps({'swift_proxy': {'pipeline': self.pipeline}})
        return Response(
            request=req, body=body, content_type="application/json")

    def DISABLED(self, req):
        """Returns a 503 response with "DISABLED BY FILE" in the body."""
        return Response(request=req, status=503, body="DISABLED BY FILE",
                        content_type="text/plain")

    def __call__(self, env, start_response):
        req = Request(env)
        try:
            if req.path == '/middlewarecheck':
                handler = self.GET
                if self.disable_path and os.path.exists(self.disable_path):
                    handler = self.DISABLED
                return handler(req)(env, start_response)
        except UnicodeError:
            # definitely, this is not /middlewarecheck
            pass
        return self.app(env, start_response)


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def middlewarecheck_filter(app):
        return MiddlewareCheckMiddleware(app, conf)
    return middlewarecheck_filter
