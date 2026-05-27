import io
from pathlib import Path

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakeProcStdin:
    def __init__(self):
        self.stdin = io.BytesIO()


def test_send_writes_header_and_payload():
    proc = FakeProcStdin()
    client = JDTLSClient(["java"], workspace=Path("."))
    # inject fake proc
    client._proc = proc
    client.notify("test/method", {"a": 1})
    proc.stdin.seek(0)
    out = proc.stdin.read().decode("utf-8")
    assert "Content-Length:" in out
    assert '"test/method"' in out
