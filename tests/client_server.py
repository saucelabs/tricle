import time

import monocle
from monocle import _o
from monocle.stack.network import add_service, Service, Client, ConnectionLost
from monocle.util import sleep
from o_test import test


@_o
def handle_echo(conn):
    while True:
        try:
            message = yield conn.read_until(b'\r\n')
            message = message.decode('utf-8')
        except ConnectionLost:
            break
        yield conn.write(("you said: %s\r\n" % message.strip()).encode())


@test
@_o
def test_lots_of_messages():
    add_service(Service(handle_echo, port=8000))
    try:
        client = Client()
        yield client.connect('localhost', 8000)
        t = time.time()
        for x in range(1000):
            msg = "hello, world #%s!" % x
            yield client.write(msg.encode() + b'\r\n')
            echo_result = yield client.read_until(b"\r\n")
            echo_result = echo_result.decode('utf-8')
            assert echo_result.strip() == "you said: %s" % msg, echo_result
        print('10000 loops in %.2fs' % (time.time() - t))
    finally:
        client.close()
        yield sleep(0.1)
