"""Minimal JDT LS client: subprocess manager + JSON-RPC transport for LSP.

This is a lightweight, well-documented skeleton that provides the
essential primitives we need to start JDT LS, send framed LSP messages
over stdio, and perform basic request/response handling. It is not a
fully-featured LSP client — it's intentionally small to be testable and
expandable.
"""
from __future__ import annotations

import json
import threading
import subprocess
import itertools
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Dict, Optional


class JDTLSClient:
    """Start/stop a JDT LS process and send/receive LSP JSON-RPC messages.

    Usage (basic):
      client = JDTLSClient(cmd, workspace)
      client.start()
      client.initialize()
      client.open_text_document(path, source)
      resp = client.request('textDocument/documentSymbol', { ... })
      client.shutdown()
    """

    def __init__(
        self, cmd: list[str], workspace: Path, timeout: float = 10.0
    ) -> None:
        self.cmd = cmd
        self.workspace = workspace
        self.timeout = timeout

        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._writer_lock = threading.Lock()
        self._pending: Dict[int, Queue] = {}
        self._id_iter = itertools.count(1)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.workspace),
        )
        if not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("Failed to open JDT LS stdio pipes")

        self._running = True
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True
        )
        self._reader_thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        try:
            # Best-effort shutdown; server may also support shutdown/exit.
            self._proc.terminate()
        finally:
            self._running = False
            if self._proc:
                self._proc.wait(timeout=5)

    def _reader_loop(self) -> None:
        assert self._proc and self._proc.stdout
        stream = self._proc.stdout
        while self._running:
            try:
                header = stream.readline()
            except OSError:
                break
            if not header:
                break
            # Expect header like: b'Content-Length: 123\r\n'
            if not header.startswith(b"Content-Length:"):
                # consume and ignore unexpected lines
                continue
            try:
                length = int(header.split(b":")[1].strip())
            except (IndexError, ValueError):
                continue
            # consume the blank line
            _ = stream.readline()
            try:
                body = stream.read(length)
            except OSError:
                continue

            try:
                msg = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            # dispatch response if it has an id
            if "id" in msg:
                q = self._pending.get(int(msg["id"]))
                if q:
                    q.put(msg)
            # notifications are ignored by default; adapters can extend

    def _send(self, payload: Dict[str, Any]) -> None:
        assert self._proc and self._proc.stdin
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        with self._writer_lock:
            self._proc.stdin.write(header)
            self._proc.stdin.write(data)
            self._proc.stdin.flush()

    def request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous request: send request and wait for response.

        Raises `TimeoutError` on timeout.
        """
        req_id = next(self._id_iter)
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        q: Queue = Queue(maxsize=1)
        self._pending[req_id] = q
        try:
            self._send(payload)
            try:
                resp = q.get(timeout=self.timeout)
            except Empty as exc:
                raise TimeoutError(f"LSP request {method} timed out") from exc
            return resp
        finally:
            self._pending.pop(req_id, None)

    def notify(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    # Convenience helpers (minimal):
    def initialize(
        self, root_uri: str, client_name: str = "uml_planterator"
    ) -> Dict[str, Any]:
        params = {
            "processId": None,
            "rootUri": root_uri,
            "capabilities": {},
            "clientInfo": {"name": client_name},
        }
        return self.request("initialize", params)

    def shutdown(self) -> None:
        try:
            self.request("shutdown")
        except TimeoutError:
            # ignore shutdown timeout
            pass
        try:
            self.notify("exit")
        finally:
            self.stop()

    def open_text_document(self, path: Path, text: str) -> None:
        uri = f"file://{path.resolve()}"
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": "java",
                "version": 1,
                "text": text,
            }
        }
        self.notify("textDocument/didOpen", params)
