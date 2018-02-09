import types

from asyncio import sleep  # exported

from monocle.stack.eventloop import queue_task
from monocle.callback import Callback


def next_tick():
    cb = Callback()
    cb(None)
    return cb


def immediate(val):
    cb = Callback()
    cb(val)
    return cb


def delayed(seconds, val):
    cb = Callback()
    queue_task(seconds, cb, val)
    return cb
