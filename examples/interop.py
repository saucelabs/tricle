import asyncio
import monocle
import monocle.util
from monocle import Return
from monocle import _o
from monocle.script_util import run


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
