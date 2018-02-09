import sys

import monocle
from monocle import _o
monocle.init(sys.argv[1])

from monocle.stack import eventloop
from monocle.stack.network import add_service
from monocle.stack.network.http import HttpHeaders, HttpServer

@_o
def hello_http(req):
    raise Exception("test")
    yield None

add_service(HttpServer(8088, handler=hello_http))
eventloop.run()
