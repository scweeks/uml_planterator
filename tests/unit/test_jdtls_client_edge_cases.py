import io
import subprocess
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeProcBase:
    def __init__(self, to_read: bytes = b""):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(to_read)
        self.stderr = io.BytesIO()
        self._terminated = False

    def terminate(self):
        self._terminated = True

    def wait(self, *_, **__):
        return 0


def test_malformed_header_is_ignored(monkeypatch):
    # Header doesn't start with Content-Length
    data = b"X-Header: 10\r\n\r\n{'a':1}"
    proc = FakeProcBase(data)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))
    client.start()
    client.stop()
    assert True


def test_readline_raises_oserror(monkeypatch):
    class BadStdout:
        def readline(self):
            raise OSError()

    proc = FakeProcBase()
    proc.stdout = BadStdout()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))
    client.start()
    client.stop()
    assert True


def test_request_timeout_raises(monkeypatch):
    # No response will be injected; short timeout
    proc = FakeProcBase()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."), timeout=0.1)
    client.start()
    try:
        try:
            client.request("doesNotExist")
            raised = False
        except TimeoutError:
            raised = True
        assert raised
    finally:
        client.stop()
