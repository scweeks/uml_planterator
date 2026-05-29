"""Minimal JDT LS client: subprocess manager + JSON-RPC transport for LSP.

This is a lightweight, well-documented skeleton that provides the
essential primitives we need to start JDT LS, send framed LSP messages
over stdio, and perform basic request/response handling. It is not a
fully-featured LSP client — it's intentionally small to be testable and
expandable.
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from queue import Empty, Queue
from typing import Any


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
        self,
        cmd: list[str],
        workspace: Path,
        timeout: float = 10.0,
        proc: subprocess.Popen | None = None,
        proc_factory: Callable[..., Any] | None = None,
    ) -> None:
        # Basic input validation to avoid shell-injection style misuse:
        if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
            raise ValueError("cmd must be a list of strings")
        if not isinstance(workspace, Path):
            raise ValueError("workspace must be a pathlib.Path")

        self.cmd = cmd
        self.workspace = workspace
        self.timeout = timeout
        self._proc: subprocess.Popen | None = proc
        self._proc_factory = proc_factory
        self._reader_thread: threading.Thread | None = None
        self._writer_lock = threading.Lock()
        self._pending: dict[int, Queue] = {}
        self._id_iter = itertools.count(1)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self.workspace.mkdir(parents=True, exist_ok=True)
        # Allow injected proc or factory for deterministic tests
        if self._proc is None:
            if self._proc_factory is not None:
                self._proc = self._proc_factory(self.cmd, self.workspace)
            else:
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
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        try:
            # Best-effort shutdown; server may also support shutdown/exit.
            if self._proc:
                self._proc.terminate()
        finally:
            self._running = False
            if self._proc:
                self._proc.wait(timeout=5)

    def _reader_loop(self) -> None:
        assert self._proc and self._proc.stdout
        stream = self._proc.stdout
        fd = None
        try:
            fd = stream.fileno()
            try:
                os.set_blocking(fd, False)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                # If not supported, fall back to blocking reads but keep checks
                fd = None
        except (OSError, ValueError, AttributeError):
            fd = None

        buffer = bytearray()
        while self._running:
            try:
                if fd is not None:
                    try:
                        chunk = stream.read(4096)
                    except (BlockingIOError, OSError):
                        chunk = b""
                else:
                    # Fallback: blocking read small amount to remain responsive
                    chunk = stream.read(1024)
            except OSError:
                break

            if not chunk:
                # If process terminated, exit loop
                try:
                    poll = getattr(self._proc, "poll", None)
                    if poll is not None and callable(poll) and poll() is not None:
                        break
                except Exception:
                    # If fake proc lacks poll or raises, assume still running
                    pass
                # No data available; sleep briefly and continue
                time.sleep(0.01)
                continue

            buffer.extend(chunk)

            # Try to parse any complete messages in the buffer
            while True:
                # Find end of header line
                idx = buffer.find(b"\r\n")
                if idx == -1:
                    break
                header_line = bytes(buffer[: idx + 2])
                # Remove header line from buffer
                del buffer[: idx + 2]
                if not header_line.lower().startswith(b"content-length:"):
                    # ignore unexpected header lines and continue parsing
                    continue
                try:
                    length = int(header_line.split(b":", 1)[1].strip())
                except (IndexError, ValueError):
                    continue
                # Ensure blank line present
                if len(buffer) < 2:
                    # wait for more data
                    break
                if buffer[:2] == b"\r\n":
                    del buffer[:2]
                # Wait until full body available
                if len(buffer) < length:
                    # restore header and wait for more data
                    # re-prepend header_line and blank; simpler to wait
                    # and let the next loop iteration fill buffer
                    # (we already removed header to avoid partial reparse)
                    break
                body = bytes(buffer[:length])
                del buffer[:length]
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

    def _send(self, payload: dict[str, Any]) -> None:
        assert self._proc and self._proc.stdin
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        with self._writer_lock:
            self._proc.stdin.write(header)
            self._proc.stdin.write(data)
            self._proc.stdin.flush()

    def request(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Synchronous request: send request and wait for response.

        Raises `TimeoutError` on timeout.
        """
        req_id = next(self._id_iter)
        payload: dict[str, Any] = {
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

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    # Convenience helpers (minimal):
    def initialize(
        self, root_uri: str, client_name: str = "uml_planterator"
    ) -> dict[str, Any]:
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
