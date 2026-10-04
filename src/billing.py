"""Provider adapters (Stripe, Lemon Squeezy, PayPal), database-backed entitlements, and checkout links.

Nothing here calls a payment provider or moves money. Adapters verify a webhook's signature with the provider's own
scheme and translate it into one normalised event:

    {id, type, subject, plan, period_end, customer?}     type: payment.succeeded | subscription.cancelled | payment.refunded

`subject` is our user id. It reaches the provider through the checkout link (see `checkout_url`) and comes back in
the webhook. Webhooks need a small always-on HTTP endpoint (Streamlit cannot receive them); see docs/PAYMENTS.md.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Protocol
from urllib.parse import urlencode

from db import Database

TOLERANCE_SECONDS = 300
GRACE_SECONDS = 3 * 24 * 3600  # a renewal that is a little late should not lock a student out mid-essay


class WebhookError(ValueError):
    """Bad signature or unreadable payload. Respond 400 and do not retry-spam."""


class Provider(Protocol):
    name: str

    def parse_webhook(self, body: bytes, headers: dict[str, str], secret: str, now: float | None = None) -> dict | None:
        """Verify and normalise. Return None for events we do not act on. Raise WebhookError when invalid."""


def _lower(headers: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def _json(body: bytes) -> dict:
    try:
        data = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise WebhookError("payload is not JSON") from exc
    if not isinstance(data, dict):
        raise WebhookError("payload is not an object")
    return data


def _iso_to_epoch(text: str) -> int:
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())


class StripeProvider:
    """Stripe-Signature: t=<ts>,v1=<hmac_sha256(secret, "<ts>.<body>")>."""

    name = "stripe"

    def parse_webhook(self, body: bytes, headers: dict[str, str], secret: str, now: float | None = None) -> dict | None:
        header = _lower(headers).get("stripe-signature", "")
        if not secret or not header:
            raise WebhookError("missing signature")
        parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
        try:
            ts = int(parts["t"])
        except (KeyError, ValueError) as exc:
            raise WebhookError("bad signature header") from exc
        if abs((now if now is not None else time.time()) - ts) > TOLERANCE_SECONDS:
            raise WebhookError("stale signature")
        expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, parts.get("v1", "")):
            raise WebhookError("invalid signature")
        event = _json(body)
        obj = event.get("data", {}).get("object", {})
        kind = event.get("type", "")
        base = {"id": str(event.get("id", "")), "customer": obj.get("customer")}
        if not base["id"]:
            raise WebhookError("missing event id")
        if kind == "checkout.session.completed" and obj.get("payment_status") == "paid":
            plan = (obj.get("metadata") or {}).get("plan", "student")
            span = 35 * 24 * 3600 if obj.get("mode") == "subscription" else 365 * 24 * 3600
            return {**base, "type": "payment.succeeded", "subject": obj.get("client_reference_id"), "plan": plan,
                    "period_end": int(event.get("created", time.time())) + span}
        if kind == "invoice.paid":
            line = (obj.get("lines", {}).get("data") or [{}])[0]
            end = (line.get("period") or {}).get("end")
            if end:
                return {**base, "type": "payment.succeeded", "subject": None, "plan": "student", "period_end": int(end) + GRACE_SECONDS}
        if kind == "customer.subscription.deleted":
            return {**base, "type": "subscription.cancelled", "subject": None, "plan": "student", "period_end": 0}
        if kind == "charge.refunded":
            return {**base, "type": "payment.refunded", "subject": None, "plan": "student", "period_end": 0}
        return None


class LemonSqueezyProvider:
    """X-Signature: hex hmac_sha256(secret, body). User id travels as checkout custom data `user_id`."""

    name = "lemonsqueezy"

    def parse_webhook(self, body: bytes, headers: dict[str, str], secret: str, now: float | None = None) -> dict | None:
        sig = _lower(headers).get("x-signature", "")
        if not secret or not sig:
            raise WebhookError("missing signature")
        if not hmac.compare_digest(hmac.new(secret.encode(), body, hashlib.sha256).hexdigest(), sig):
            raise WebhookError("invalid signature")
        event = _json(body)
        meta = event.get("meta", {})
        name = meta.get("event_name", "")
        data = event.get("data", {})
        attrs = data.get("attributes", {})
        custom = meta.get("custom_data") or {}
        sub_id = str(data.get("id", ""))
        event_id = f"ls:{name}:{sub_id}:{attrs.get('updated_at', attrs.get('created_at', ''))}"
        subject = custom.get("user_id")
        plan = custom.get("plan", "student")
        base = {"id": event_id, "subject": subject, "plan": plan, "customer": f"ls:{attrs.get('customer_id', sub_id)}"}
        if name in ("subscription_created", "subscription_payment_success", "subscription_resumed"):
            end = attrs.get("renews_at") or attrs.get("ends_at")
            if end:
                return {**base, "type": "payment.succeeded", "period_end": _iso_to_epoch(end) + GRACE_SECONDS}
        if name == "subscription_expired":
            return {**base, "type": "subscription.cancelled", "period_end": 0}
        if name in ("order_refunded", "subscription_payment_refunded"):
            return {**base, "type": "payment.refunded", "period_end": 0}
        return None


class PayPalProvider:
    """PayPal verifies webhooks by calling its API (verify-webhook-signature), which needs network and credentials.

    So this adapter takes an injected `verifier(body, headers) -> bool`. The deployment wires the real PayPal call
    in; tests inject a stub. Without a verifier it fails closed.
    """

    name = "paypal"

    def __init__(self, verifier=None):
        self.verifier = verifier

    def parse_webhook(self, body: bytes, headers: dict[str, str], secret: str, now: float | None = None) -> dict | None:
        if self.verifier is None or not self.verifier(body, headers):
            raise WebhookError("invalid signature")
        event = _json(body)
        kind = event.get("event_type", "")
        res = event.get("resource", {})
        base = {"id": str(event.get("id", "")), "subject": res.get("custom_id") or res.get("custom"), "plan": "student",
                "customer": f"pp:{res.get('id', '')}"}
        if not base["id"]:
            raise WebhookError("missing event id")
        if kind in ("PAYMENT.SALE.COMPLETED", "BILLING.SUBSCRIPTION.ACTIVATED"):
            return {**base, "type": "payment.succeeded", "period_end": int(time.time()) + 35 * 24 * 3600}
        if kind in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED", "BILLING.SUBSCRIPTION.SUSPENDED"):
            return {**base, "type": "subscription.cancelled", "period_end": 0}
        if kind == "PAYMENT.SALE.REFUNDED":
            return {**base, "type": "payment.refunded", "period_end": 0}
        return None


PROVIDERS: dict[str, Provider] = {"stripe": StripeProvider(), "lemonsqueezy": LemonSqueezyProvider()}


class DbEntitlements:
    """Who has paid until when, plus processed event ids (idempotency) and provider-customer links."""

    def __init__(self, db: Database):
        self.db = db

    def seen(self, event_id: str) -> bool:
        return self.db.one("SELECT 1 FROM events WHERE id=?", (event_id,)) is not None

    def record_event(self, event_id: str) -> None:
        self.db.execute("INSERT INTO events (id, received_at) VALUES (?,?)", (event_id, int(time.time())))

    def grant(self, subject: str, plan: str, expires_at: int) -> None:
        self.db.execute(
            "INSERT INTO grants (subject, plan, expires_at) VALUES (?,?,?) "
            "ON CONFLICT (subject) DO UPDATE SET plan=excluded.plan, expires_at=excluded.expires_at",
            (subject, plan, int(expires_at)),
        )

    def revoke(self, subject: str) -> None:
        self.db.execute("DELETE FROM grants WHERE subject=?", (subject,))

    def get(self, subject: str, now: float | None = None) -> dict | None:
        row = self.db.one("SELECT plan, expires_at FROM grants WHERE subject=?", (subject,))
        if not row or row[1] <= (now if now is not None else time.time()):
            return None
        return {"subject": subject, "plan": row[0], "expires_at": int(row[1])}

    def link_customer(self, customer: str, user_id: str) -> None:
        self.db.execute(
            "INSERT INTO customers (provider_customer, user_id) VALUES (?,?) "
            "ON CONFLICT (provider_customer) DO UPDATE SET user_id=excluded.user_id", (customer, user_id))

    def user_for_customer(self, customer: str) -> str | None:
        row = self.db.one("SELECT user_id FROM customers WHERE provider_customer=?", (customer,))
        return row[0] if row else None

    def commit(self) -> None:
        self.db.commit()


def apply_event(store: DbEntitlements, event: dict) -> str:
    """Apply a normalised event once. Returns 'applied', 'duplicate' or 'ignored'."""
    if store.seen(event["id"]):
        return "duplicate"
    subject = event.get("subject")
    customer = event.get("customer")
    if subject and customer:
        store.link_customer(customer, subject)
    elif customer and not subject:
        subject = store.user_for_customer(customer)
    result = "ignored"
    if subject:
        if event["type"] == "payment.succeeded":
            store.grant(subject, event["plan"], int(event["period_end"]))
            result = "applied"
        elif event["type"] in ("subscription.cancelled", "payment.refunded"):
            store.revoke(subject)
            result = "applied"
    store.record_event(event["id"])
    store.commit()
    return result


def process_provider_webhook(store: DbEntitlements, provider: Provider, secret: str, body: bytes,
                             headers: dict[str, str], now: float | None = None) -> str:
    event = provider.parse_webhook(body, headers, secret, now)
    return "ignored" if event is None else apply_event(store, event)


def checkout_url(provider: str, user_id: str, email: str, plan: str = "student") -> str | None:
    """Hosted checkout link for this user, built from a link you create in the provider dashboard.

    STRIPE_PAYMENT_LINK / LEMONSQUEEZY_CHECKOUT_URL / PAYPAL_SUBSCRIBE_URL come from the environment. Returns None
    when that provider is not configured, so the UI can hide the button.
    """
    env = {"stripe": "STRIPE_PAYMENT_LINK", "lemonsqueezy": "LEMONSQUEEZY_CHECKOUT_URL", "paypal": "PAYPAL_SUBSCRIBE_URL"}
    base = os.getenv(env.get(provider, ""), "")
    if not base:
        return None
    if provider == "stripe":
        query = {"client_reference_id": user_id, "prefilled_email": email}
    elif provider == "lemonsqueezy":
        query = {"checkout[email]": email, "checkout[custom][user_id]": user_id, "checkout[custom][plan]": plan}
    else:
        query = {"custom_id": user_id}
    return f"{base}{'&' if '?' in base else '?'}{urlencode(query)}"


def configured_providers() -> list[str]:
    return [p for p in ("stripe", "lemonsqueezy", "paypal") if checkout_url(p, "x", "x@example.com")]
