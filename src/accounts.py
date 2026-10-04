"""Accounts: email and password sign-up, sessions, lockout, and student verification (.ac.uk).

No third-party services. Passwords use scrypt with a per-user salt. Session and email tokens are random and only
their SHA-256 hash is stored, so a database leak does not leak live sessions. Sending email is behind the `Mailer`
protocol so any provider (Resend, Postmark, SES, SMTP) can be plugged in later.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

import audit
from db import Database

SESSION_SECONDS = 14 * 24 * 3600
VERIFY_SECONDS = 24 * 3600
LOCKOUT_FAILS = 5
LOCKOUT_WINDOW = 15 * 60
MIN_PASSWORD = 10
RESET_SECONDS = 3600
TERMS_VERSION = "2026-10-draft"
COMMON_PASSWORDS = {"password123", "1234567890", "qwertyuiop", "letmein123", "iloveyou123", "password1234", "admin12345",
                    "welcome123", "0123456789", "passw0rd123", "qwerty12345", "abc1234567"}
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)$")
# UK universities use .ac.uk. Extra domains (other countries, schools) come from STUDENT_EMAIL_SUFFIXES.
DEFAULT_STUDENT_SUFFIXES = (".ac.uk",)


class AccountError(ValueError):
    """A problem the user can fix. The message is safe to show."""


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleMailer:
    """Collects messages instead of sending them. Default until an email provider is configured."""

    def __init__(self) -> None:
        self.outbox: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append((to, subject, body))


@dataclass(frozen=True)
class User:
    id: str
    email: str
    display_name: str
    student_verified: bool
    student_domain: str | None


def normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def student_suffixes() -> tuple[str, ...]:
    extra = tuple(s.strip().lower() for s in os.getenv("STUDENT_EMAIL_SUFFIXES", "").split(",") if s.strip())
    return DEFAULT_STUDENT_SUFFIXES + extra


def is_student_email(email: str, suffixes: tuple[str, ...] | None = None) -> bool:
    match = EMAIL_RE.match(normalise_email(email))
    if not match:
        return False
    domain = match.group(1)
    return any(domain.endswith(s) and domain != s.lstrip(".") for s in (suffixes or student_suffixes()))


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def check_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=2**14, r=8, p=1, dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, actual)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AccountService:
    def __init__(self, db: Database, mailer: Mailer | None = None):
        self.db = db
        self.mailer: Mailer = mailer or ConsoleMailer()

    # --- sign up and sign in -------------------------------------------------
    def _check_password_rules(self, email: str, password: str) -> None:
        if len(password) < MIN_PASSWORD:
            raise AccountError(f"Use a password of at least {MIN_PASSWORD} characters.")
        if password.lower() in COMMON_PASSWORDS or password.lower() == email or len(set(password)) < 4:
            raise AccountError("That password is too easy to guess. Pick something longer or less common.")

    def register(self, email: str, password: str, display_name: str = "", now: float | None = None,
                 accept_terms: bool = True) -> User:
        now_i = int(now if now is not None else time.time())
        email = normalise_email(email)
        if not EMAIL_RE.match(email):
            raise AccountError("Enter a valid email address.")
        self._check_password_rules(email, password)
        if not accept_terms:
            raise AccountError("Please accept the Terms and Privacy Policy.")
        if self.db.one("SELECT 1 FROM users WHERE email=? AND deleted_at IS NULL", (email,)):
            raise AccountError("An account with that email already exists.")
        user_id = uuid.uuid4().hex
        self.db.execute(
            "INSERT INTO users (id, email, pw_hash, display_name, created_at, terms_accepted_at, terms_version) VALUES (?,?,?,?,?,?,?)",
            (user_id, email, hash_password(password), display_name.strip()[:60], now_i, now_i, TERMS_VERSION),
        )
        self.db.commit()
        audit.record(self.db, "register", user_id, now=now_i)
        self._send_email_verification(user_id, email, now_i)
        return self.get_user(user_id)  # type: ignore[return-value]

    def _recent_failures(self, email: str, now: int) -> int:
        row = self.db.one(
            "SELECT COUNT(*) FROM login_attempts WHERE email=? AND ok=0 AND attempted_at>?", (email, now - LOCKOUT_WINDOW)
        )
        return int(row[0]) if row else 0

    def login(self, email: str, password: str, now: float | None = None) -> tuple[User, str]:
        """Return (user, session_token). Same error for unknown email and wrong password."""
        now_i = int(now if now is not None else time.time())
        email = normalise_email(email)
        if self._recent_failures(email, now_i) >= LOCKOUT_FAILS:
            audit.record(self.db, "login_locked", detail=audit.fingerprint(email), now=now_i)
            raise AccountError("Too many attempts. Try again in 15 minutes.")
        row = self.db.one("SELECT id, pw_hash FROM users WHERE email=? AND deleted_at IS NULL", (email,))
        ok = bool(row) and check_password(password, row[1])  # type: ignore[index]
        if not row:
            hash_password(password)  # keep timing similar for unknown emails
        self.db.execute("INSERT INTO login_attempts (email, attempted_at, ok) VALUES (?,?,?)", (email, now_i, int(ok)))
        self.db.commit()
        if not ok or not row:
            audit.record(self.db, "login_fail", detail=audit.fingerprint(email), now=now_i)
            raise AccountError("Email or password is not right.")
        audit.record(self.db, "login_ok", row[0], now=now_i)
        token = secrets.token_urlsafe(32)
        self.db.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
            (_token_hash(token), row[0], now_i, now_i + SESSION_SECONDS),
        )
        self.db.commit()
        return self.get_user(row[0]), token  # type: ignore[return-value]

    def user_for_session(self, token: str, now: float | None = None) -> User | None:
        if not token:
            return None
        now_i = int(now if now is not None else time.time())
        row = self.db.one("SELECT user_id, expires_at FROM sessions WHERE token_hash=?", (_token_hash(token),))
        if not row or row[1] <= now_i:
            return None
        return self.get_user(row[0])

    def logout(self, token: str) -> None:
        row = self.db.one("SELECT user_id FROM sessions WHERE token_hash=?", (_token_hash(token),))
        self.db.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))
        self.db.commit()
        if row:
            audit.record(self.db, "logout", row[0])

    # --- login email verification and password reset ---------------------------
    def _issue_token(self, user_id: str, purpose: str, seconds: int, now_i: int) -> str:
        token = secrets.token_urlsafe(24)
        self.db.execute("INSERT INTO email_tokens (token_hash, user_id, purpose, expires_at) VALUES (?,?,?,?)",
                        (_token_hash(token), user_id, purpose, now_i + seconds))
        self.db.commit()
        return token

    def _send_email_verification(self, user_id: str, email: str, now_i: int) -> None:
        token = self._issue_token(user_id, "verify_email", VERIFY_SECONDS, now_i)
        self.mailer.send(email, "Confirm your email", f"Your confirmation code is: {token}\nIt expires in 24 hours.")

    def _consume(self, user_id: str | None, token: str, purpose: str, now_i: int) -> str:
        """Mark a one-time token used and return its user id. Raises AccountError if invalid, used or expired."""
        row = self.db.one("SELECT user_id, expires_at, used_at FROM email_tokens WHERE token_hash=? AND purpose=?",
                          (_token_hash(token.strip()), purpose))
        if not row or row[2] is not None or row[1] <= now_i or (user_id is not None and row[0] != user_id):
            raise AccountError("That code is not valid or has expired.")
        self.db.execute("UPDATE email_tokens SET used_at=? WHERE token_hash=?", (now_i, _token_hash(token.strip())))
        return str(row[0])

    def is_email_verified(self, user_id: str) -> bool:
        row = self.db.one("SELECT email_verified_at FROM users WHERE id=?", (user_id,))
        return bool(row and row[0] is not None)

    def confirm_email(self, user_id: str, token: str, now: float | None = None) -> None:
        now_i = int(now if now is not None else time.time())
        self._consume(user_id, token, "verify_email", now_i)
        self.db.execute("UPDATE users SET email_verified_at=? WHERE id=?", (now_i, user_id))
        self.db.commit()
        audit.record(self.db, "email_verified", user_id, now=now_i)

    def request_password_reset(self, email: str, now: float | None = None) -> None:
        """Always looks the same to the caller, so it cannot be used to discover which emails have accounts."""
        now_i = int(now if now is not None else time.time())
        email = normalise_email(email)
        row = self.db.one("SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (email,))
        if row:
            token = self._issue_token(row[0], "reset", RESET_SECONDS, now_i)
            self.mailer.send(email, "Reset your password", f"Your reset code is: {token}\nIt expires in 1 hour. If you did not ask, ignore this.")
            audit.record(self.db, "password_reset_requested", row[0], now=now_i)

    def reset_password(self, email: str, token: str, new_password: str, now: float | None = None) -> None:
        now_i = int(now if now is not None else time.time())
        email = normalise_email(email)
        self._check_password_rules(email, new_password)
        row = self.db.one("SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (email,))
        if not row:
            raise AccountError("That code is not valid or has expired.")
        self._consume(row[0], token, "reset", now_i)
        self.db.execute("UPDATE users SET pw_hash=? WHERE id=?", (hash_password(new_password), row[0]))
        self.db.execute("DELETE FROM sessions WHERE user_id=?", (row[0],))  # sign out everywhere
        self.db.execute("DELETE FROM login_attempts WHERE email=?", (email,))
        self.db.commit()
        audit.record(self.db, "password_reset_done", row[0], now=now_i)

    def get_user(self, user_id: str) -> User | None:
        row = self.db.one(
            "SELECT id, email, display_name, student_verified_at, student_domain FROM users WHERE id=? AND deleted_at IS NULL",
            (user_id,),
        )
        if not row:
            return None
        return User(row[0], row[1], row[2], row[3] is not None, row[4])

    # --- student verification ------------------------------------------------
    def start_student_verification(self, user_id: str, student_email: str, now: float | None = None) -> None:
        """Email a one-time link/code to a student address. Raises AccountError if it is not a student domain."""
        now_i = int(now if now is not None else time.time())
        student_email = normalise_email(student_email)
        if not is_student_email(student_email):
            raise AccountError("Use your university email (for UK students, an address ending .ac.uk).")
        token = secrets.token_urlsafe(24)
        purpose = f"student:{student_email}"
        self.db.execute(
            "INSERT INTO email_tokens (token_hash, user_id, purpose, expires_at) VALUES (?,?,?,?)",
            (_token_hash(token), user_id, purpose, now_i + VERIFY_SECONDS),
        )
        self.db.commit()
        self.mailer.send(student_email, "Confirm your student email",
                         f"Your confirmation code is: {token}\nIt expires in 24 hours. If you did not ask for this, ignore it.")

    def confirm_student(self, user_id: str, token: str, now: float | None = None) -> User:
        now_i = int(now if now is not None else time.time())
        row = self.db.one(
            "SELECT purpose, expires_at, used_at FROM email_tokens WHERE token_hash=? AND user_id=?",
            (_token_hash(token.strip()), user_id),
        )
        if not row or row[2] is not None or row[1] <= now_i or not row[0].startswith("student:"):
            raise AccountError("That code is not valid or has expired.")
        student_email = row[0].split(":", 1)[1]
        domain = student_email.split("@", 1)[1]
        self.db.execute("UPDATE email_tokens SET used_at=? WHERE token_hash=?", (now_i, _token_hash(token.strip())))
        self.db.execute("UPDATE users SET student_domain=?, student_verified_at=? WHERE id=?", (domain, now_i, user_id))
        self.db.commit()
        audit.record(self.db, "student_verified", user_id, detail=domain, now=now_i)
        return self.get_user(user_id)  # type: ignore[return-value]

    # --- data rights (UK GDPR) -----------------------------------------------
    def export_data(self, user_id: str) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise AccountError("Account not found.")
        progress = self.db.all("SELECT exercise_id, best_score, attempts, passed FROM progress WHERE user_id=?", (user_id,))
        favourites = self.db.all("SELECT prompt_id FROM favourites WHERE user_id=?", (user_id,))
        saved = self.db.all("SELECT title, body, tags FROM workspace_prompts WHERE user_id=?", (user_id,))
        audit.record(self.db, "data_export", user_id)
        return {
            "email": user.email, "display_name": user.display_name, "student_domain": user.student_domain,
            "workspace_prompts": [{"title": r[0], "body": r[1], "tags": r[2]} for r in saved],
            "progress": [dict(zip(("exercise_id", "best_score", "attempts", "passed"), r, strict=True)) for r in progress],
            "favourites": [r[0] for r in favourites],
        }

    def delete_account(self, user_id: str) -> None:
        """Erase personal data. Keeps an anonymous tombstone row so foreign references stay consistent."""
        for table in ("sessions", "email_tokens", "progress", "favourites", "workspace_prompts", "ai_usage"):
            self.db.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))  # noqa: S608 - fixed table names
        self.db.execute("DELETE FROM customers WHERE user_id=?", (user_id,))
        self.db.execute("DELETE FROM grants WHERE subject=?", (user_id,))
        self.db.execute(
            "UPDATE users SET email=?, pw_hash='', display_name='', student_domain=NULL, deleted_at=? WHERE id=?",
            (f"deleted-{user_id}@invalid", int(time.time()), user_id),
        )
        self.db.commit()
        audit.record(self.db, "account_deleted", user_id)
