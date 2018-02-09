import sys
import monocle
monocle.init(sys.argv[1])

from monocle.script_util import run

from monocle import _o, Return
from monocle.callback import Callback
from monocle import Return, InvalidYieldException
import monocle.util

import asyncio


@_o
def square(x):
    monocle.util.sleep(0)
    yield Return(x * x)

async def four():
    print('Running in two')
    await asyncio.sleep(0)
    print('Done with two')
    return await square(2).future

@_o
def eight():
    x = yield four()
    yield Return(x)


async def fail():
    raise Exception("boo")
    print(await square(2).future)


@_o
def invalid_yield():
    yield "this should fail"


@_o
def main():
    value = yield eight()
    print(value)
    yield fail()

run(main)
