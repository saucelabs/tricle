import sys
import asyncio
import asyncio.base_futures
import collections
import logging

logging.basicConfig(stream=sys.stderr,
                    format="%(message)s")
log = logging.getLogger("monocle")


class Callback(collections.abc.Awaitable):
    """
    A monocle Callback object, implemented using asyncio.Future.
    """

    def __init__(self):
        self.future = asyncio.Future()

    def add(self, handler):
        if not callable(handler):
            raise TypeError("'%s' object is not callable" % type(handler).__name__)

        def callback_handler(fut):
            e = fut.exception()
            if e:
                handler(e)
            else:
                handler(fut.result())
        self.future.add_done_callback(callback_handler)

    def __call__(self, result):
        assert not hasattr(self, 'result'), "Already called back"
        self.result = result
        try:
            if isinstance(result, BaseException):
                self.future.set_exception(result)
            else:
                self.future.set_result(result)
        except asyncio.base_futures.InvalidStateError:
            # this should never happen, because we checked that we
            # haven't been called back, above. But, it does, so log
            # some info about it. Gotta love this future API:
            r = None
            e = None
            c = self.future.cancelled()
            if not c:
                e = self.future.exception()
                if not e:
                    r = self.future.result()
            log.exception("future already called back in Callback! future result: c: %s, e: %s, r: %s; cb result: %s",
                          c, e, r, self.result)
            raise

    def __await__(self):
        return self.future.__await__()


def defer(result):
    cb = Callback()
    cb(result)
    return cb
