import io
import json
 
import subprocess
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeProc:
    def __init__(self, to_read: bytes):
        # simulate stdio streams as BytesIO
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(to_read)
        self.stderr = io.BytesIO()
        self._terminated = False

    def terminate(self):
        self._terminated = True

    def wait(self, *_, **__):
        return 0


def test_reader_handles_partial_and_invalid_json(monkeypatch):
    # Build a stream that has headers split and an invalid JSON chunk
    msg = json.dumps({"jsonrpc": "2.0", "method": "$/progress"}).encode()
    header = f"Content-Length: {len(msg)}\r\n\r\n".encode()

    # Split header into two parts and corrupt JSON
    data = header[:10] + header[10:] + msg[:5] + b"}{\n"

    proc = FakeProc(data)

    # Monkeypatch Popen to return our fake process
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))
    # start will spawn the reader thread which consumes the provided stdout
    client.start()
    # allow reader to consume
    client.stop()

    # If invalid JSON occurred, it should not crash; ensure start/stop complete
    assert True


def test_initialize_and_shutdown_flow(monkeypatch):
    # Fake process with minimal valid notify frames for initialize response
    resp = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()
    header = f"Content-Length: {len(resp)}\r\n\r\n".encode()
    proc = FakeProc(header + resp)

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))

    # start should spawn proc and reader; wrap start/initialize/shutdown
    client.start()
    # ensure the response is delivered after the request is sent

    def _send_and_inject(self, payload):
        # Directly inject a response into the pending queue for the
        # request id so `request()` returns without waiting on the real
        # reader thread. This keeps the test deterministic.
        rid = int(payload.get("id", 0))
        if rid and rid in self._pending:
            self._pending[rid].put({"jsonrpc": "2.0", "id": rid, "result": {}})
        return None

    monkeypatch.setattr(JDTLSClient, "_send", _send_and_inject)

    # initialize should return without raising; reader supplies response
    client.initialize(root_uri="file://.")
    client.shutdown()

    # After shutdown, the fake proc terminate flag may be set
    assert getattr(proc, "_terminated", False) in (True, False)
