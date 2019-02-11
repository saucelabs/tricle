from monocle import _o

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service


@_o
def echo(conn):
    their_message = yield conn.readline()
    print("received: %r" % their_message.decode())
    yield conn.write("you said: %s\r\n" % their_message.decode().strip())
    print("response written")


add_service(Service(echo, 7050))
eventloop.run()
