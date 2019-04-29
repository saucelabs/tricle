import monocle
from monocle import Return, InvalidYieldException
from monocle import _o
from monocle.script_util import run


@_o
def square(x):
    yield Return(x * x)
    print("not reached")


@_o
def fail():
    raise Exception("oroutine boo")
    print((yield square(2)))


@_o
def invalid_yield():
    yield "this should fail"


@_o
def ordinary():
    return "non-coroutines work"


@_o
def main():
    value = yield ordinary()
    print(value)
    value = yield square(5)
    print(value)
    try:
        yield fail()
    except Exception as e:
        print("Caught exception:", type(e), str(e))
        assert str(e) == "oroutine boo"
    try:
        yield invalid_yield()
    except InvalidYieldException as e:
        print("Caught exception:", type(e), str(e))
    else:
        assert False


def func_fail():
    raise Exception("func boo")


@_o
def example():
    monocle.launch(fail)
    monocle.launch(func_fail)
    yield main()


run(example)
