from monocle import _o

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service


@_o
def echo(conn):
    their_message = yield conn.readline()
    their_message = their_message.decode()
    print("received: %r" % their_message)
    yield conn.write("you said: %s\r\n" % their_message.strip())
    print("response written")


add_service(Service(echo, 7050))
eventloop.run()
