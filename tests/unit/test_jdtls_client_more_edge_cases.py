import io
import subprocess
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeProc2:
    def __init__(self, to_read: bytes = b""):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(to_read)
        self.stderr = io.BytesIO()
        self._terminated = False

    def terminate(self):
        self._terminated = True

    def wait(self, *_, **__):
        return 0


def test_malformed_content_length_and_partial_body(monkeypatch):
    # Content-Length is non-numeric, then header with length larger than body
    msg = b"{notjson}"
    hdr1 = b"Content-Length: abc\r\n\r\n"
    hdr2 = b"Content-Length: 100\r\n\r\n"
    data = hdr1 + hdr2 + msg

    proc = FakeProc2(data)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))
    client.start()
    client.stop()
    assert True


def test_notification_without_id_is_ignored(monkeypatch):
    # Notification has no 'id' field and should be ignored safely
    body = b'{"jsonrpc":"2.0","method":"$/progress","params":{}}'
    header = f"Content-Length: {len(body)}\r\n\r\n".encode()
    proc = FakeProc2(header + body)
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: proc)

    client = JDTLSClient(["java"], workspace=Path("."))
    client.start()
    client.stop()
    assert True
