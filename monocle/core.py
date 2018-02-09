import sys
import types
import logging
import functools
import asyncio

from .callback import Callback, defer

logging.basicConfig(stream=sys.stderr,
                    format="%(message)s")
log = logging.getLogger("monocle")


class Return(object):
    def __init__(self, *args):
        # mimic the semantics of the return statement
        if len(args) == 0:
            self.value = None
        elif len(args) == 1:
            self.value = args[0]
        else:
            self.value = args

    def __repr__(self):
        return "<%s.%s object at 0x%x; value: %s>" % (self.__class__.__module__,
                                                      self.__class__.__name__,
                                                      id(self),
                                                      repr(self.value))


class InvalidYieldException(TypeError):
    pass


# @_o
def _o(f):
    @functools.wraps(f)
    def coroutine_wrapper(*a, **k):
        gen_f = f(*a, **k)
        if not isinstance(gen_f, types.GeneratorType):
            if isinstance(gen_f, Callback):
                return gen_f
            return defer(gen_f)

        # make a coroutine that runs the monocle oroutine generator,
        # translating yielded Callbacks and Returns to the way these
        # things are handled in asyncio
        @functools.wraps(f)
        async def gen_wrapper():
            r = None
            e = None
            while True:
                try:
                    if e is not None:
                        r = gen_f.throw(e)
                        e = None
                    else:
                        r = gen_f.send(r)
                except StopIteration:
                    return None

                if isinstance(r, Return):
                    return r.value

                try:
                    if isinstance(r, Callback):
                        r = await r.future
                    elif (asyncio.iscoroutine(r) or
                          isinstance(r, asyncio.Future)):
                        r = await r
                    else:
                        raise InvalidYieldException(
                            "Unexpected value '%s' of type '%s' yielded from o-routine '%s'.  "
                            "O-routines can only yield Callback, coroutine, Future, and Return types." % (r, type(r), f))
                except Exception as e2:
                    e = e2

        fut = asyncio.ensure_future(gen_wrapper())
        cb = Callback()

        def _trigger_callback_with_future(fut):
            e = fut.exception()
            if e:
                cb(e)
            else:
                cb(fut.result())

        fut.add_done_callback(_trigger_callback_with_future)
        return cb

    return coroutine_wrapper
o = _o


def log_exception(msg="", elide_internals=None):
    log.exception(msg)


@_o
def launch(oroutine, *args, **kwargs):
    try:
        cb = oroutine(*args, **kwargs)
        if (not isinstance(cb, (Callback, asyncio.Future)) and
            not asyncio.iscoroutine(cb)):
            yield Return(cb)

        r = yield cb
        yield Return(r)
    except GeneratorExit:
        raise
    except Exception:
        log_exception()
