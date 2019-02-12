import time

from monocle import _o
from monocle.script_util import run
from monocle.stack.network import add_service, Service, Client, ConnectionLost


@_o
def handle_echo(conn):
    while True:
        try:
            message = yield conn.read_until('\r\n')
            message = message.decode().strip()
        except ConnectionLost:
            break
        yield conn.write("you said: %s\r\n" % message)


@_o
def do_echos():
    client = Client()
    try:
        yield client.connect('localhost', 8000)
        t = time.time()
        for x in range(10000):
            msg = "hello, world #%s!" % x
            yield client.write(msg + '\r\n')
            echo_result = yield client.read_until('\r\n')
            assert echo_result.decode().strip() == "you said: %s" % msg
        print('10000 loops in %.2fs' % (time.time() - t))
    finally:
        client.close()


add_service(Service(handle_echo, port=8000, bindaddr="localhost"))
run(do_echos)
