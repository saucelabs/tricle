from o_test import test
from contextlib import contextmanager

from monocle import _o, Return
from monocle.stack import network
from monocle.stack.network import http
from monocle.util import sleep

payload_multiplier = 1024 * 1024 * 10

@_o
def default_handler(conn):
    data = 'Hello, World!'
    headers = http.HttpHeaders()
    headers.add('Content-Length', len(data))
    headers.add('Content-Type', 'text/plain')
    headers.add('Connection', 'close')
    yield Return(200, headers, data)


@contextmanager
def http_server_running(port, handler=default_handler):
    service = http.HttpServer(port, handler=handler, max_body_str_len=payload_multiplier * 10)
    network.add_service(service)
    try:
        yield
    finally:
        service.stop()


@contextmanager
def http_client():
    client = http.HttpClient()
    try:
        yield client
    finally:
        client.close()


@test
@_o
def test_client():
    addr = '127.0.0.1'
    port = 5556
    with http_server_running(port):
        yield sleep(0.1)
        with http_client() as client:
            yield client.connect(addr, port)
            r = yield client.request('/')
            assert r.code == '200', r.code  # should this be an int?


@test
@_o
def test_large_requests():
    addr = '127.0.0.1'
    port = 5557
    recv_body = []

    @_o
    def _handler(conn):
        recv_body.append(conn.body)
        data = 'Hello, World!'
        headers = http.HttpHeaders()
        headers.add('Content-Length', len(data))
        headers.add('Content-Type', 'text/plain')
        headers.add('Connection', 'close')
        yield Return(200, headers, data)
    with http_server_running(port, handler=_handler):
        yield sleep(0.1)
        with http_client() as client:
            yield client.connect(addr, port)
            send_body = 'x' * payload_multiplier
            r = yield client.request('/', method='POST', body='x' * payload_multiplier)
            assert recv_body and recv_body[0] == send_body
