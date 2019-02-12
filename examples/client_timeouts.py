import monocle

from monocle import _o

from monocle.stack import eventloop
from monocle.stack.network import Client


@_o
def main():
    c = Client()
    """
    yield c.connect('google.com', 80)
    yield c.write("GET / HTTP/1.0\r\n\r\n")
    x = None
    c.timeout = 0
    try:
        x = yield c.read(40000)
    except Exception, e:
        print str(e)
    print x
    """
    c.timeout = 1
    yield c.connect('google.com', 80)
    yield c.write("GET / HTTP/1.0\r\n\r\n")
    c.timeout = 0
    x = yield c.read(40000)
    print(x)
    eventloop.halt()


monocle.launch(main)
eventloop.run()
