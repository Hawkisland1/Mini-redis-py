# mini-redis-py

[![Build Status](https://dev.azure.com/mini-redis-py/mini-redis-py/_apis/build/status%2FHawkisland1.Mini-redis-py?branchName=main)](https://dev.azure.com/mini-redis-py/mini-redis-py/_build/latest?definitionId=1&branchName=main)

A Redis-like in-memory key-value server implemented from scratch in Python, using [gevent](http://www.gevent.org/) for concurrency. It implements a subset of the RESP-style wire protocol, a handful of core commands, and append-only file persistence with log replay on startup.

Originally based on [this tutorial](https://charlesleifer.com/blog/building-a-simple-redis-server-with-python/), then rewritten for Python 3, split into modules, covered with tests, and extended with persistence.

## Features

- Custom binary wire protocol (RESP-inspired): simple strings, errors, integers, bulk strings, arrays, and dicts
- Core commands: `GET`, `SET`, `DELETE`, `FLUSH`, `MGET`, `MSET`
- Concurrent client handling via gevent's greenlets and a connection pool
- Append-only file (AOF) persistence — every write is logged, and the log is replayed on startup to rebuild state
- Test suite covering protocol encode/decode round-trips, command logic, and persistence across restarts
- Containerized with Docker
- CI via Azure Pipelines — tests run automatically on every push to `main`

## Project structure

```
protocol.py   # Wire protocol: parsing requests, serializing responses
server.py     # Server class: command dispatch, in-memory store, persistence
client.py     # Client class: connects to the server, sends commands
main.py       # Entry point: starts the server
tests/        # pytest suite
```

## Running it

Install dependencies:

```
pip install gevent pytest
```

Start the server:

```
python main.py
```

In a separate terminal/Python session, use the client:

```python
from client import Client

client = Client()
client.mset('k1', 'v1', 'k2', 'v2')
client.get('k1')          # b'v1'
client.mget('k1', 'k2')   # [b'v1', b'v2']
client.delete('k1')       # 1
client.get('k1')          # None
```

Run the tests:

```
pytest -v
```

## How it works

Requests and responses are framed using a simple type-prefixed binary protocol, similar to Redis's own RESP:

- `+` simple string
- `-` error
- `:` integer
- `$` bulk string (length-prefixed, binary-safe)
- `*` array
- `%` dict

For example, the command `SET k1 v1` is sent over the wire as an array of bulk strings:

```
*3\r\n$3\r\nSET\r\n$2\r\nk1\r\n$2\r\nv1\r\n
```

The `ProtocolHandler` class in `protocol.py` handles both directions: parsing incoming bytes into Python objects (`handle_request`), and serializing Python objects back into wire-format bytes (`write_response`).

The `Server` class in `server.py` holds all state in a single in-memory dict (`self._kv`) and dispatches parsed commands to the appropriate method (`get`, `set`, `delete`, etc.).

### Persistence

Every mutating command (`SET`, `DELETE`, `MSET`, `FLUSH`) is appended to an append-only log file (`database.aof` by default), encoded using the exact same protocol used for client/server communication — the log is effectively a recording of commands as if they'd been sent over the wire. On startup, the server replays this log through its own command dispatcher (`get_response`) to rebuild the in-memory state, so replay logic never drifts out of sync with live command behavior.

## Design notes / what I'd change at scale

- **Concurrency model**: the in-memory dict isn't thread-safe. gevent's cooperative scheduling avoids real preemptive-threading race conditions here, but a version built for true parallelism (multiple processes or OS threads) would need per-key locking or a different concurrency strategy entirely (e.g. sharding the keyspace).
- **Log compaction**: the append-only log grows forever and is replayed in full on every startup. A production version would need periodic compaction — rewriting the log to just the current state — the same way Redis's own AOF rewrite works.
- **Durability guarantees**: writes are appended to the log but not explicitly `fsync`'d, so a crash immediately after a write could lose that entry. A stricter durability mode would trade write latency for calling `fsync` after each append.
- **Single point of failure**: there's no replication — one server, one copy of the data. A distributed version would need to handle replica sync and failover.
- **Mixed key types after replay**: commands issued directly in Python use `str` keys/values, but anything read back from the append-only log (or received over the network) comes through the wire protocol as `bytes`. This means the same logical key can exist as `'k1'` or `b'k1'` depending on how it entered the system — a real inconsistency I found while testing persistence. A production version would normalize all keys to `bytes` (or `str`, decoded consistently) at the point of ingestion, rather than leaving the type ambiguous.

## Extending this project

Possible next steps: additional commands (`EXPIRE`, `LPUSH`/`LPOP`), a pub/sub mechanism, a pub/sub mechanism, and deploying the container to Azure (Container Instances or App Service) for a live, reachable instance.