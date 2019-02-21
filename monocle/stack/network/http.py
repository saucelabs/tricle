# -*- coding: utf-8 -*-
#
# by Steven Hazel

import asyncio
import base64
import collections
import http.cookies
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request
from typing import Optional

import aiohttp.web
import multidict
from aiohttp import ClientSession
from aiohttp.web_request import Request

from monocle import _o, Return, log_exception
from monocle.stack.network import Service, SSLService

try:
    from monocle.stack.network import SSLClient
except ImportError:
    pass

log = logging.getLogger(__name__)


class HttpException(Exception):
    pass


class HttpHeaders(multidict.CIMultiDict):
    def get_list(self, *a, **k):
        # synonym; should be deprecated
        return getall(*a, **k)


class HttpRequest(object):
    def __init__(self, proto='HTTP/1.0', host=None, method=None,
                 uri=None, args=None, remote_ip=None, headers=None,
                 body: Optional[str] = None, body_file: Optional[bytes] = None, cookies=None):
        self.aiohttp_request: Request = None
        self.proto = proto
        self.host = host
        self.method = method
        self.uri = uri
        self.remote_ip = remote_ip
        self.headers = headers
        if body:
            self.body_file = body.encode()
        else:
            self.body_file = body_file

        self.path, _, self.query = uri.partition('?')
        self.query_args = urllib.parse.parse_qs(self.query, keep_blank_values=True)
        self.args = args

        if cookies is not None:
            self.cookies = cookies
        else:
            self.cookies = {}
            for cookie in self.headers.getall("cookie", []):
                try:
                    for name, morsel in http.cookies.BaseCookie(cookie).items():
                        self.cookies[name] = morsel.value
                except http.cookies.CookieError:
                    pass

    @classmethod
    async def from_aiohttp_request(cls, request: Request):
        self = cls(
            proto=(request.scheme.upper() +
                   "/%s.%s" % (request.version.major, request.version.minor)),
            host=request.host,
            method=request.method,
            uri=request.raw_path,
            args=request.post(),
            remote_ip=request.transport.get_extra_info('peername')[0],
            headers=request.headers,
            body_file=await request.read(),
            cookies=request.cookies)
        self.aiohttp_request = request
        return self

    def __repr__(self):
        return "<%s (%s %s %s, headers=%s)>" % (
            self.__class__.__name__, self.method, self.path, self.proto, self.headers)

    def get_basic_auth(self):
        if 'authorization' not in self.headers:
            return None, None
        auth = self.headers["authorization"]
        try:
            method, b64 = auth.split(" ")
            if method.lower() != "basic":
                return None, None
            username, password = base64.decodestring(b64).split(':', 1)
        except Exception:
            # parsing error; no valid auth
            return None, None
        return username, password

    @property
    def body(self) -> Optional[str]:
        if self.body_file:
            return self.body_file.decode()

        return None


class HttpResponse(object):
    def __init__(self, code, msg=None, headers=None, body=None, proto=None):
        self.code = code
        self.msg = msg
        self.headers = headers or HttpHeaders()
        self.body = body
        self.proto = proto or 'HTTP/1.1'

    @classmethod
    async def from_aiohttp_response(cls, response):
        self = cls(
            code=str(response.status),
            msg=response.reason,
            headers=response.headers,
            body=await response.text(),
            proto='HTTP' + "/%s.%s" % (response.version.major, response.version.minor))
        self.aiohttp_response = response
        return self


class HttpClient(object):
    DEFAULT_PORTS = {'http': 80,
                     'https': 443}

    def __init__(self,
                 scheme: str = None,
                 host: str = None,
                 port: int = None,
                 is_proxy: bool = False):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.is_proxy = is_proxy
        self.session: ClientSession = None

    async def connect(self, host, port,
                      scheme='http',
                      timeout=None,  # this parameter is deprecated
                      is_proxy=False):
        """*** DEPRECATED ***
            Provide the values via constructor instead.
        """
        if not self.is_closed():
            await self.session.close()

        self.scheme = scheme
        self.host = host
        self.port = port
        self.is_proxy = is_proxy
        self.session = ClientSession(connector=aiohttp.TCPConnector())

    async def request(self, url, headers=None, method='GET', body=None):
        parts = urllib.parse.urlsplit(url)

        if self.is_proxy:
            host = parts.netloc
            path = url
        else:
            if parts.scheme and parts.scheme != self.scheme:
                raise HttpException("URL is %s but connection is %s" %
                                    (parts.scheme, self.scheme))

            host = parts.netloc
            if not host:
                host = self.host
                if self.port != self.DEFAULT_PORTS[self.scheme]:
                    host += ":%s" % self.port

            path = parts.path
            if parts.query:
                path += '?' + parts.query
        async with self.session.request(
                method,
                self.scheme + '://' + host + path,
                headers=headers,
                data=body) as resp:
            return await HttpResponse.from_aiohttp_response(resp)

    def close(self):
        asyncio.ensure_future(self.session.close())

    def is_closed(self):
        return self.session is None or self.session.closed

    @classmethod
    async def query(cls, url, headers=None, method='GET', body=None):
        async with aiohttp.request(method, url, headers=headers, data=body) as resp:
            monocle_resp = await HttpResponse.from_aiohttp_response(resp)
            return monocle_resp


# Takes a response return value like:
# "this is a body"
# 404
# (200, "this is a body")
# (200, {"headers": "here"}, "this is a body")
#
# ...and converts that to a full (code, headers, body) tuple.
def extract_response(value):
    if isinstance(value, str):
        return (200, HttpHeaders(), value)
    if isinstance(value, int):
        return (value, HttpHeaders(), "")
    if len(value) == 2:
        return (value[0], HttpHeaders(), value[1])
    return value


class HttpRouter(object):
    named_param_re = re.compile(r':([^\/\?\*\:]+)')

    def __init__(self):
        self.routes = collections.defaultdict(list)

    @classmethod
    def path_matches(cls, path, pattern):
        m = pattern.match(path)
        if not m:
            return False, None
        if not m.end() == len(path):
            # must match the whole string
            return False, None
        return True, m.groupdict()

    def mk_decorator(self, method, pattern, add_head=False):
        if not hasattr(pattern, 'match'):
            pattern = re.escape(pattern)
            pattern = pattern.replace(r'\?', '?')
            pattern = pattern.replace(r'\:', ':')
            pattern = pattern.replace(r'\_', '_')
            pattern = pattern.replace(r'\/', '/')
            pattern = pattern.replace(r'\*', '.*')
            pattern = self.named_param_re.sub(r'(?P<\1>[^/]+)', pattern)
            pattern = re.compile("^" + pattern + "$")

        def decorator(f):
            handler = f
            if not asyncio.iscoroutinefunction(f):
                # don't require the @_o decorator *and* the HttpServer decorator
                handler = _o(f)
            self.routes[method].append((pattern, handler))
            if add_head:
                self.routes['HEAD'].append((pattern, handler))
            return handler

        return decorator

    def get(self, pattern, add_head=True):
        return self.mk_decorator('GET', pattern, add_head=add_head)

    def post(self, pattern):
        return self.mk_decorator('POST', pattern)

    def put(self, pattern):
        return self.mk_decorator('PUT', pattern)

    def delete(self, pattern):
        return self.mk_decorator('DELETE', pattern)

    def head(self, pattern):
        return self.mk_decorator('HEAD', pattern)

    def options(self, pattern):
        return self.mk_decorator('OPTIONS', pattern)

    def patch(self, pattern):
        return self.mk_decorator('PATCH', pattern)

    def route_match(self, req):
        for pattern, handler in self.routes[req.method]:
            match, kwargs = self.path_matches(urllib.parse.unquote(req.path),
                                              pattern)
            if match:
                return handler, kwargs
        return None, None

    @_o
    def request_handler_wrapper(self, req, handler, **kwargs):
        resp = yield handler(req, **kwargs)
        yield Return(resp)

    @_o
    def handle_request(self, req):
        before = time.time()
        resp = None

        handler, kwargs = self.route_match(req)
        try:
            if handler:
                resp = yield self.request_handler_wrapper(req, handler, **kwargs)
            elif self.handler:
                resp = yield self.request_handler_wrapper(req, self.handler)
            else:
                resp = (404, {}, "")
        except Exception:
            log_exception()
            resp = (500, {}, "500 Internal Server Error")
        after = time.time()

        content_length = 0
        if len(resp) > 2:
            content_length = len(resp[2])

        log.info("[%s] %s %s %s -> %s (%s bytes, %.0fms); %s",
                 req.remote_ip,
                 req.method, req.path, req.proto,
                 resp[0], content_length, (after - before) * 1000,
                 req.headers.get('user-agent'))

        yield Return(resp)


class HttpServer(Service, HttpRouter):
    def __init__(self, port, handler=None, bindaddr="", backlog=128,
                 max_body_str_len: int = 1024 * 1024):
        HttpRouter.__init__(self)
        self.port = port
        self.bindaddr = bindaddr
        self.backlog = backlog
        self.app = aiohttp.web.Application(client_max_size=max_body_str_len)
        self.handler = handler

        async def _handler(request: Request):
            monocle_request = await HttpRequest.from_aiohttp_request(request)
            resp = await self.handle_request(monocle_request)
            status, headers, body = extract_response(resp)
            if 'content-type' not in {k.lower() for k in headers.keys()}:
                headers['Content-Type'] = 'text/html'
            headers = {(k, str(v)) for k, v in headers.items()}
            return aiohttp.web.Response(status=status, headers=headers, body=body)

        self.app.router.add_route('*', r'/{path:.*}', _handler)

    async def _add(self):
        self._server = await asyncio.get_event_loop().create_server(
            self.app.make_handler(),
            host=self.bindaddr,
            port=self.port,
            backlog=self.backlog)


class HttpsServer(SSLService, HttpRouter):
    def __init__(self, port, ssl_options, handler=None, bindaddr="", backlog=128,
                 max_body_str_len=1024 * 1024):
        HttpRouter.__init__(self)
        SSLService.__init__(self, handler, port, bindaddr=bindaddr, backlog=backlog)
