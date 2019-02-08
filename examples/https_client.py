import monocle
from monocle import _o
from monocle.stack import eventloop
from monocle.stack.network.http import HttpClient


@_o
def main():
    c = HttpClient()
    yield c.connect('google.com', 443, scheme='https')
    resp = yield c.request('/')
    print(resp.body)
    yield c.close()


monocle.launch(main)
eventloop.run()
