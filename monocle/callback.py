import asyncio
import collections


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
        if isinstance(result, BaseException):
            self.future.set_exception(result)
        else:
            self.future.set_result(result)

    def __await__(self):
        return self.future.__await__()


def defer(result):
    cb = Callback()
    cb(result)
    return cb
