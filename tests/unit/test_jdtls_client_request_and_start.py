import io
import json
import threading
import time
from queue import Queue
from pathlib import Path
import subprocess
import importlib

import pytest

from uml_planterator.lsp.jdtls_client import JDTLSClient


class FakePopen:
    def __init__(self, stdout_bytes: bytes = b""):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(stdout_bytes)
        self.stderr = io.BytesIO()
        self._terminated = False

    def terminate(self):
        self._terminated = True

    def wait(self, timeout=None):
        return 0


def test_request_with_fake_send(monkeypatch):
    client = JDTLSClient(cmd=["/bin/true"], workspace=Path('.'))

    def fake_send(payload):
        # simulate server reply into pending queue
        rid = int(payload.get("id"))
        resp = {"jsonrpc": "2.0", "id": rid, "result": {"ok": True}}
        q = client._pending.get(rid)
        if q:
            q.put(resp)

    monkeypatch.setattr(client, "_send", fake_send)
    res = client.request("test/method", {"x": 1})
    assert res["result"]["ok"] is True


def test_start_and_reader_dispatch(monkeypatch):
    # prepare a message with id=1 framed
    msg = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"pong": True}}).encode("utf-8")
    framed = f"Content-Length: {len(msg)}\r\n\r\n".encode("ascii") + msg
    fake = FakePopen(stdout_bytes=framed)

    def fake_popen(cmd, stdin, stdout, stderr, cwd):
        return fake

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    client = JDTLSClient(cmd=["java"], workspace=Path('.'))
    # prepare a pending queue for id=1
    q = Queue(maxsize=1)
    client._pending[1] = q
    client.start()
    # give reader thread a moment
    time.sleep(0.1)
    # reader should have placed the message
    msg_out = q.get(timeout=1)
    assert msg_out.get("result", {}).get("pong") is True
    client.stop()
