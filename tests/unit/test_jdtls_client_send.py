import io
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeProc:
    def __init__(self):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()


def test_send_writes_content_length_and_payload():
    fake = FakeProc()
    client = JDTLSClient(cmd=["/bin/true"], workspace=Path("."))
    client._proc = fake  # inject fake process
    payload = {"jsonrpc": "2.0", "method": "test"}
    client._send(payload)
    data = fake.stdin.getvalue()
    assert b"Content-Length:" in data
    assert b'"method":"test"' in data


def test_notify_builds_payload(monkeypatch):
    client = JDTLSClient(cmd=["/bin/true"], workspace=Path("."))
    seen = {}

    def fake_send(p):
        seen["payload"] = p

    monkeypatch.setattr(client, "_send", fake_send)
    client.notify("textDocument/didOpen", {"foo": 1})
    assert seen["payload"]["method"] == "textDocument/didOpen"
    assert seen["payload"]["params"]["foo"] == 1
