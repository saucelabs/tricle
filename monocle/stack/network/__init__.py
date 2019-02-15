# -*- coding: utf-8 -*-
#
# by Steven Hazel

import asyncio
from typing import Union

from monocle import _o, Return, launch
from monocle.callback import Callback
from monocle.stack import eventloop


class ConnectionException(Exception):
    pass


class ConnectionTimeout(asyncio.TimeoutError, ConnectionException):
    pass


"""  *** DEPRECATED *** For generic errors, please use ConnectionException instead."""
ConnectionLost = ConnectionException


class Connection(object):
    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self.writing = False
        self.flush_cb = Callback()
        self.timeout = None
        self._closed = False

    async def read_some(self) -> bytes:
        # there's no equivalent of this "read as much as can be read
        # quickly" in the asychio streaming API -- just set a
        # reasonable limit
        try:
            return await asyncio.wait_for(self._reader.read(65536), self.timeout)
        except asyncio.TimeoutError as e:
            raise ConnectionTimeout() from e

    async def read(self, size) -> bytes:
        try:
            return await asyncio.wait_for(self._reader.readexactly(size), self.timeout)
        except asyncio.TimeoutError as e:
            raise ConnectionTimeout() from e

    async def read_until(self, s: Union[bytes, str]) -> bytes:
        if isinstance(s, str):
            s = s.encode()
        try:
            return await asyncio.wait_for(self._reader.readuntil(s), self.timeout)
        except asyncio.TimeoutError as e:
            raise ConnectionTimeout() from e

    async def readline(self) -> bytes:
        try:
            return await asyncio.wait_for(self._reader.readline(), self.timeout)
        except asyncio.TimeoutError as e:
            raise ConnectionTimeout() from e

    async def write(self, data: Union[bytes, str]) -> None:
        if isinstance(data, str):
            data = data.encode()
        self._writer.write(data)
        await self.flush()

    async def flush(self):
        return await self._writer.drain()

    def close(self):
        self._closed = True
        if self._writer:
            self._writer.close()

    def is_closed(self):
        # note that this actually doesn't return True until all data
        # has been read
        return self._closed


class Service(object):
    def __init__(self, handler, port, bindaddr="", backlog=128):
        async def _handler(reader, writer):
            connection = Connection(reader, writer)
            try:
                await launch(handler, connection)
            finally:
                writer.close()

        self._handler = _handler
        self.port = port
        self.bindaddr = bindaddr
        self.backlog = backlog
        self._server = None

    async def _add(self):
        self._server = await asyncio.start_server(
            self._handler,
            host=self.bindaddr,
            port=self.port,
            limit=104857600,
            backlog=self.backlog)
        print(self._server)

    async def stop(self):
        self._server.close()
        await self._server.wait_closed()


class SSLService(Service):

    def __init__(self, handler, ssl_options, port, bindaddr="", backlog=128):
        Service.__init__(self, handler, port, bindaddr, backlog)
        self.ssl_options = ssl_options

    def _add(self):
        cf = ssl.DefaultOpenSSLContextFactory(self.ssl_options['keyfile'],
                                              self.ssl_options['certfile'])
        self._twisted_listening_port = reactor.listenSSL(
            self.port, self.factory, cf,
            backlog=self.backlog,
            interface=self.bindaddr)


class Client(Connection):
    def __init__(self, *args, **kwargs):
        Connection.__init__(self, None, None, *args, **kwargs)

    async def connect(self, host, port):
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host=host, port=port, limit=104857600),
                                                    self.timeout)
            self._reader = reader
            self._writer = writer
        except asyncio.TimeoutError as e:
            raise ConnectionTimeout(f"failed to establish connection to {host}:{port} within {self.timeout}s") from e


class SSLClient(Client):

    def __init__(self, ssl_options=None):
        if ssl_options is None:
            ssl_options = {}
        Connection.__init__(self)
        self.ssl_options = ssl_options

    def _connect_to_reactor(self, host, port, factory, timeout):
        reactor.connectSSL(host, port, factory,
                           SSLContextFactory(self.ssl_options),
                           timeout=timeout)


def add_service(service):
    return asyncio.ensure_future(service._add())
