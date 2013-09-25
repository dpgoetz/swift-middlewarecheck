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

import os
import shutil
import tempfile
import unittest

from swift.common.swob import Request, Response
from middlewarecheck import middleware


class FakeApp(object):
    def __call__(self, env, start_response):
        req = Request(env)
        return Response(request=req, body='FAKE APP')(
            env, start_response)


class ExcConfigParser(object):

    def read(self, path):
        raise IOError(
            '[Errno 2] No such file or directory: {path}'.format(path=path))


class SetConfigParser(object):

    PIPELINE = ('healthcheck middlewarecheck cache tempauth '
                'proxy-logging proxy-server')

    def read(self, path):
        return True

    def get(self, section, option):
        if section == 'pipeline:main':
            if option == 'pipeline':
                return self.PIPELINE


class TestMiddlewareCheck(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.disable_path = os.path.join(self.tempdir, 'dont-taze-me-bro')
        self.got_statuses = []

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def get_app(self, app, global_conf, **local_conf):
        factory = middleware.filter_factory(global_conf, **local_conf)
        return factory(app)

    def start_response(self, status, headers):
        self.got_statuses.append(status)

    def test_middlewarecheck(self):
        middleware.ConfigParser = SetConfigParser
        req = Request.blank(
            '/middlewarecheck', environ={'REQUEST_METHOD': 'GET'})
        app = self.get_app(FakeApp(), {})
        resp = app(req.environ, self.start_response)
        self.assertEquals(['200 OK'], self.got_statuses)

        pipeline = SetConfigParser.PIPELINE.split(' ')
        pipeline = ', '.join(
            '"{middleware}"'.format(middleware=m) for m in pipeline)

        self.assertEquals(
            resp, ['{{"swift_proxy": {{'
                   '"pipeline": [{pipeline}]}}}}'.format(pipeline=pipeline)])

    def test_middlewarecheck_disabled(self):
        open(self.disable_path, 'w')
        middleware.ConfigParser = SetConfigParser
        req = Request.blank(
            '/middlewarecheck', environ={'REQUEST_METHOD': 'GET'})
        app = self.get_app(FakeApp(), {}, disable_path=self.disable_path)
        resp = app(req.environ, self.start_response)
        self.assertEquals(['503 Service Unavailable'], self.got_statuses)
        self.assertEquals(resp, ['DISABLED BY FILE'])

    def test_middlewarecheck_missing_config(self):
        middleware.ConfigParser = ExcConfigParser
        req = Request.blank(
            '/middlewarecheck', environ={'REQUEST_METHOD': 'GET'})
        app = self.get_app(FakeApp(), {})
        resp = app(req.environ, self.start_response)
        self.assertEquals(['503 Service Unavailable'], self.got_statuses)
        self.assertEquals(resp, ['Service Unavailable'])


if __name__ == '__main__':
    unittest.main()
