from monocle import _o, launch
from monocle.script_util import run
from monocle.util import sleep


@_o
def req():
    yield sleep(1)


def die():
    raise Exception("boom")


@_o
def fifth():
    die()


def fourth():
    return fifth()


@_o
def third():
    yield fourth()


def second():
    return third()


@_o
def first():
    yield second()


@_o
def first_evlp():
    yield sleep(1)
    yield req()
    yield launch(second)  # won't crash


run(first_evlp)
