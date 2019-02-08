from monocle import _o
from monocle.stack import eventloop
from monocle.stack.network import add_service
from monocle.stack.network.http import HttpServer


@_o
def hello_http(req):
    raise Exception("test")


add_service(HttpServer(8088, handler=hello_http))
eventloop.run()
