import json
from queue import Queue
 
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeStdout:
    def __init__(self, header: bytes, body: bytes):
        self._header = header
        self._body = body
        self._state = 0

    def readline(self):
        # First call: header, second call: blank line, subsequent: empty
        if self._state == 0:
            self._state = 1
            return self._header
        if self._state == 1:
            self._state = 2
            return b"\r\n"
        return b""

    def read(self, _length):
        return self._body


class FakeProc:
    def __init__(self, stdout):
        self.stdout = stdout


def test_reader_handles_non_content_header():
    client = JDTLSClient(["java"], Path("."))
    client._proc = FakeProc(stdout=FakeStdout(b"Random: 1\r\n", b""))
    client._running = True
    # Should exit cleanly without raising
    client._reader_loop()


def test_reader_handles_invalid_length():
    client = JDTLSClient(["java"], Path("."))
    client._proc = FakeProc(stdout=FakeStdout(b"Content-Length: abc\r\n", b""))
    client._running = True
    client._reader_loop()


def test_reader_oserror_on_read():
    class BadStdout(FakeStdout):
        def read(self, length):
            raise OSError()

    client = JDTLSClient(["java"], Path("."))
    client._proc = FakeProc(stdout=BadStdout(b"Content-Length: 10\r\n", b""))
    client._running = True
    client._reader_loop()


def test_reader_invalid_json_and_dispatch():
    # First, invalid JSON
    client = JDTLSClient(["java"], Path("."))
    client._proc = FakeProc(stdout=FakeStdout(b"Content-Length: 4\r\n", b"nope"))
    client._running = True
    client._reader_loop()

    # Now, valid response with id and ensure it's dispatched
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode(
        "utf-8"
    )
    hdr = f"Content-Length: {len(body)}\r\n".encode("ascii")
    client = JDTLSClient(["java"], Path("."))
    client._proc = FakeProc(stdout=FakeStdout(hdr, body))
    q = Queue(maxsize=1)
    client._pending[1] = q
    client._running = True
    client._reader_loop()
    msg = q.get_nowait()
    assert msg.get("id") == 1
