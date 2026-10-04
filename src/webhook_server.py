"""Tiny stdlib HTTP service that receives payment webhooks: POST /webhooks/<provider>, GET /health.

Run separately from Streamlit:  python src/webhook_server.py   (PORT defaults to 8080)
Secrets: STRIPE_WEBHOOK_SECRET, LEMONSQUEEZY_WEBHOOK_SECRET. PayPal needs a verifier wired in (see billing.py).
"""
from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from billing import PROVIDERS, DbEntitlements, WebhookError, process_provider_webhook
from db import get_db

SECRET_ENV = {"stripe": "STRIPE_WEBHOOK_SECRET", "lemonsqueezy": "LEMONSQUEEZY_WEBHOOK_SECRET"}
MAX_BODY = 1_000_000


def handle(path: str, body: bytes, headers: dict[str, str], store: DbEntitlements) -> tuple[int, str]:
    """Pure request handler so it can be tested without a socket."""
    name = path.rstrip("/").rsplit("/", 1)[-1]
    provider = PROVIDERS.get(name)
    if not path.startswith("/webhooks/") or provider is None:
        return 404, "unknown provider"
    try:
        result = process_provider_webhook(store, provider, os.getenv(SECRET_ENV.get(name, ""), ""), body, headers)
    except WebhookError:
        return 400, "rejected"
    return 200, result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._reply(200 if self.path == "/health" else 404, "ok" if self.path == "/health" else "not found")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > MAX_BODY:
            return self._reply(413, "too large")
        body = self.rfile.read(length)
        status, text = handle(self.path, body, dict(self.headers.items()), DbEntitlements(get_db()))
        self._reply(status, text)

    def _reply(self, status: int, text: str) -> None:
        data = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:  # keep request bodies and secrets out of logs
        pass


if __name__ == "__main__":  # pragma: no cover
    HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))), Handler).serve_forever()
