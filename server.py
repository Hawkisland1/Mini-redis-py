"""
A miniature Redis-like server, based on the tutorial at:
https://charlesleifer.com/blog/building-a-simple-redis-server-with-python/

This version is updated to run on Python 3 (the original post was written
for Python 2, so string/bytes handling has been fixed throughout).
"""
from io import BytesIO
from collections import namedtuple

from gevent import socket
from gevent.pool import Pool
from gevent.server import StreamServer

from protocol import ProtocolHandler, CommandError


Error = namedtuple('Error', ('message',))


class Server(object):
    def __init__(self, host='127.0.0.1', port=31337, max_clients=64):
        self._pool = Pool(max_clients)
        self._server = StreamServer(
            (host, port),
            self.connection_handler,
            spawn=self._pool)
        self._protocol = ProtocolHandler()
        self._kv = {}
        self._commands = self.get_commands()

    def get_commands(self):
        return {
            'GET': self.get,
            'SET': self.set,
            'DELETE': self.delete,
            'FLUSH': self.flush,
            'MGET': self.mget,
            'MSET': self.mset,
        }

    def connection_handler(self, conn, address):
        socket_file = conn.makefile('rwb')

        while True:
            try:
                data = self._protocol.handle_request(socket_file)
            except Disconnect:
                break

            try:
                resp = self.get_response(data)
            except CommandError as exc:
                resp = Error(exc.args[0])

            self._protocol.write_response(socket_file, resp)

    def get_response(self, data):
        if isinstance(data, bytes):
            data = data.split()
        elif not isinstance(data, list):
            raise CommandError('Request must be list or simple string.')

        if not data:
            raise CommandError('Missing command')

        command = data[0].upper()
        if isinstance(command, bytes):
            command = command.decode('utf-8')

        if command not in self._commands:
            raise CommandError('Unrecognized command: %s' % command)

        return self._commands[command](*data[1:])

    def get(self, key):
        return self._kv.get(key)

    def set(self, key, value):
        self._kv[key] = value
        return 1

    def delete(self, key):
        if key in self._kv:
            del self._kv[key]
            return 1
        return 0

    def flush(self):
        kvlen = len(self._kv)
        self._kv.clear()
        return kvlen

    def mget(self, *keys):
        return [self._kv.get(key) for key in keys]

    def mset(self, *items):
        data = list(zip(items[::2], items[1::2]))
        for key, value in data:
            self._kv[key] = value
        return len(data)

    def run(self):
        self._server.serve_forever()

