from monocle import _o

from monocle.stack import eventloop
from monocle.util import sleep


@_o
def yielding_oroutine(x, z=1):
    yield sleep(1)
    print(x)


def nonyielding_oroutine(x, z=1):
    print(x)


@_o
def fail():
    raise Exception("whoo")
    # make this a generator function, to demonstrate exceptions work properly in this context
    yield sleep(1)


eventloop.queue_task(0, yielding_oroutine, x="oroutine worked")
eventloop.queue_task(0, nonyielding_oroutine, x="function worked")
eventloop.queue_task(0, fail)
eventloop.run()
