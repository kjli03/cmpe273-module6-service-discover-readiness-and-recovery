#!/usr/local/bin/python
"""Small HTTP inventory service for the Kubernetes readiness lab."""

from __future__ import annotations

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
READINESS_FLAG_FILE = os.environ.get("READINESS_FLAG_FILE", "/tmp/not-ready")


class InventoryHandler(BaseHTTPRequestHandler):
    request_count = 0

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/livez":
            self._send_json(200, {"status": "alive"})
            return

        if self.path == "/readyz":
            if os.path.exists(READINESS_FLAG_FILE):
                self._send_json(503, {"status": "not-ready"})
            else:
                self._send_json(200, {"status": "ready"})
            return

        if self.path != "/":
            self._send_json(404, {"error": "not found"})
            return

        type(self).request_count += 1
        self._send_json(
            200,
            {
                "service": "inventory",
                "pod": socket.gethostname(),
                "request": type(self).request_count,
            },
        )

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"{self.address_string()} - {format_string % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), InventoryHandler)
    print(f"Inventory listening on port {PORT}; pod={socket.gethostname()}", flush=True)
    server.serve_forever()
