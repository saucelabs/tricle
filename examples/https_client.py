import sys

import monocle
from monocle import _o
monocle.init(sys.argv[1])

from monocle.stack import eventloop
from monocle.stack.network.http import HttpClient

@_o
def main():
    c = HttpClient()
    yield c.connect('google.com', 443, scheme='https')
    resp = yield c.request('/')
    print(resp.body)
    c.close()

monocle.launch(main)
eventloop.run()
