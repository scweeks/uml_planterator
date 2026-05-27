import io
from types import SimpleNamespace
from pathlib import Path

import subprocess

from uml_planterator.lsp.jdtls_client import JDTLSClient


def test_start_raises_on_missing_stdio(monkeypatch, tmp_path: Path):
    # Make Popen return an object with missing stdin to trigger RuntimeError
    class FakePopen:
        def __init__(self, *_args, **_kwargs):
            self.stdin = None
            self.stdout = io.BytesIO()
            self.stderr = io.BytesIO()

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    client = JDTLSClient(["java"], tmp_path)
    try:
        raises = False
        try:
            client.start()
        except RuntimeError:
            raises = True
        assert raises
    finally:
        # ensure cleanup if partially started
        client._running = False


def test_shutdown_handles_timeout_and_calls_stop(monkeypatch, tmp_path: Path):
    client = JDTLSClient(["java"], tmp_path)

    def raising_request(*a, **k):
        raise TimeoutError()

    stopped = SimpleNamespace(called=False)

    def fake_stop():
        stopped.called = True

    monkeypatch.setattr(client, "request", raising_request)
    monkeypatch.setattr(client, "notify", lambda *a, **k: None)
    monkeypatch.setattr(client, "stop", fake_stop)

    client.shutdown()
    assert stopped.called
