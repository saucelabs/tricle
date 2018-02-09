import asyncio
import threading

from monocle import launch


class EventLoop(object):
    def __init__(self):
        self._event_loop = asyncio.get_event_loop()
        self._thread_ident = threading.get_ident()

    def queue_task(self, delay, callable, *args, **kw):
        def task():
            return launch(callable, *args, **kw)

        if threading.get_ident() != self._thread_ident:
            self._event_loop.call_soon_threadsafe(task)
        else:
            return self._event_loop.call_later(delay, task)

    def run(self):
        try:
            self._event_loop.run_forever()
        finally:
            self._event_loop.run_until_complete(
                self._event_loop.shutdown_asyncgens())
            self._event_loop.close()

    def halt(self):
        self._event_loop.stop()

evlp = EventLoop()
queue_task = evlp.queue_task
run = evlp.run
halt = evlp.halt
