# tests/test_commands.py
import pytest
from server import Server

@pytest.fixture
def server():
    """Fresh Server instance for each test, so tests don't leak state into each other."""
    return Server()

def test_set_and_get(server):
    assert server.set('k1', 'v1') == 1
    assert server.get('k1') == 'v1'

def test_get_missing_key_returns_none(server):
    assert server.get('nope') is None

def test_delete(server):
    server.set('k1', 'v1')
    assert server.delete('k1') == 1
    assert server.get('k1') is None
    assert server.delete('k1') == 0  # deleting again returns 0

def test_mset_and_mget(server):
    server.mset('k1', 'v1', 'k2', 'v2')
    assert server.mget('k1', 'k2') == ['v1', 'v2']

def test_flush(server):
    server.mset('k1', 'v1', 'k2', 'v2')
    assert server.flush() == 2
    assert server.get('k1') is None