import sys
import logging

import monocle
from monocle import _o, Return
monocle.init(sys.argv[1])

from monocle.stack import eventloop
from monocle.stack.network import add_service
from monocle.stack.network.http import HttpHeaders, HttpServer

root = logging.getLogger('')
root.setLevel(logging.DEBUG)

s = HttpServer(8089)


@s.get("/")
@s.post("/")
def hello_http(req):
    content = "Hello, World!"
    headers = HttpHeaders()
    headers.add('Content-Type', 'text/plain')
    headers.add('Set-Cookie', 'test0=blar; Path=/')
    headers.add('Set-Cookie', 'test1=blar; Path=/')
    yield Return(200, headers, content)

add_service(s)
eventloop.run()
