# tests/test_protocol.py
from io import BytesIO
from protocol import ProtocolHandler

def make_socket_file(data: bytes):
    """Helper: wraps bytes in a BytesIO so handle_request can read it like a socket."""
    return BytesIO(data)

def test_simple_string():
    protocol = ProtocolHandler()
    sock = make_socket_file(b'+OK\r\n')
    assert protocol.handle_request(sock) == b'OK'

def test_integer():
    protocol = ProtocolHandler()
    sock = make_socket_file(b':1337\r\n')
    assert protocol.handle_request(sock) == 1337

def test_bulk_string():
    protocol = ProtocolHandler()
    sock = make_socket_file(b'$5\r\nhello\r\n')
    assert protocol.handle_request(sock) == b'hello'

def test_null():
    protocol = ProtocolHandler()
    sock = make_socket_file(b'$-1\r\n')
    assert protocol.handle_request(sock) is None

def test_array():
    protocol = ProtocolHandler()
    sock = make_socket_file(b'*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n')
    assert protocol.handle_request(sock) == [b'foo', b'bar']

def test_write_response_roundtrip():
    """Write a value with the serializer, then read it back with the parser."""
    protocol = ProtocolHandler()
    buf = BytesIO()
    protocol.write_response(buf, ['SET', 'k1', 'v1'])
    buf.seek(0)
    assert protocol.handle_request(buf) == [b'SET', b'k1', b'v1']