from server import Server

def test_persistence_across_restarts(tmp_path):
    log_path = str(tmp_path / "test.aof")

    server1 = Server(log_path=log_path)
    server1.set('k1', 'v1')
    server1._log_file.close()

    server2 = Server(log_path=log_path)
    assert server2.get(b'k1') == b'v1'