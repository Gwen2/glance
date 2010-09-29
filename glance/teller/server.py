# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from webob import Request, Response, UTC
from webob.exc import HTTPAccepted, HTTPBadRequest, HTTPCreated, \
    HTTPInternalServerError, HTTPNoContent, HTTPNotFound, \
    HTTPNotModified, HTTPPreconditionFailed, \
    HTTPRequestTimeout, HTTPUnprocessableEntity, HTTPMethodNotAllowed

from glance.teller.backends import get_from_backend
from glance.teller.parallax import ParallaxAdapter


def PPRINT_OBJ(obj):
    from pprint import pprint
    pprint(obj.__dict__)
    print dir(obj)


class ImageController(object):
    """Implements the WSGI application for the Teller Image Server."""
    def __init__(self, conf):
        """
        """
        #TODO: add real lookup fn
        #self.image_lookup_fn = parallax_lookup()
        self.log_requests = conf.get('log_requests', 't')[:1].lower() == 't'

    def GET(self, request):
        try:
            uri = request.GET['uri']
        except KeyError:
            return HTTPBadRequest(body="Missing uri", request=request,
                                  content_type="text/plain")

        image = self.image_lookup_fn(uri)
        if not image:
            return HTTPNotFound(body="Image not found", request=request,
                                content_type="text/plain")

        def image_iter():
            for obj in image["objects"]:
                for chunk in get_from_backend(obj["uri"], expected_size=obj["size"]):
                    yield chunk

        return request.get_response(Response(app_iter=image_iter()))

    def __call__(self, env, start_response):
        """WSGI Application entry point for the Teller Image Server."""
        start_time = time.time()
        req = Request(env)
        if False:
            pass
        #if req.path_info == '/healthcheck':
        #    return healthcheck(req)(env, start_response)
        #elif not check_xml_encodable(req.path_info):
        #    res = HTTPPreconditionFailed(body='Invalid UTF8')
        else:
            try:
                if hasattr(self, req.method):
                    res = getattr(self, req.method)(req)
                else:
                    res = HTTPMethodNotAllowed()
            except:
                self.logger.exception('ERROR __call__ error with %s %s '
                    % (env.get('REQUEST_METHOD', '-'), env.get('PATH_INFO', '-')))
                res = HTTPInternalServerError(body=traceback.format_exc())
        trans_time = time.time() - start_time
        if self.log_requests:
            log_line = '%s - - [%s] "%s %s" %s %s "%s" "%s" %.4f' % (
                req.remote_addr,
                time.strftime('%d/%b/%Y:%H:%M:%S +0000',
                              time.gmtime()),
                req.method, req.path, res.status.split()[0],
                res.content_length or '-', req.referer or '-',
                req.user_agent or '-',
                trans_time)
            self.logger.info(log_line)
        #if req.method in ('PUT', 'DELETE'):
        #    slow = self.slow - trans_time
        #    if slow > 0:
        #        sleep(slow)
        return res(env, start_response)