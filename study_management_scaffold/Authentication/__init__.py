"""Authentication and Authorization boundary.

Owns user accounts, authentication information, and Registered User role
assignments. Database connections are obtained only through Data_Access.
"""
import hashlib
import hmac
import secrets
import sqlite3
from functools import wraps

from flask import flash, redirect, session, url_for

from Data_Access.database import get_connection
from Domain_Rules import validate_email, validate_password

ROLE_REGISTERED_USER = "Registered User"
PBKDF2_ITERATIONS = 600_000


def _hash_password(password: str) -> str:
    """Return a salted PBKDF2-HMAC-SHA256 password hash."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def init_auth() -> None:
    """Create the account table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role = 'Registered User'),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def register_user(email: str, password: str) -> int:
    """Create an account and assign the sole role automatically."""
    # Domain_Rules is the single validation gateway; DomainRuleError is a ValueError.
    normalized_email = validate_email(email)
    validate_password(password)

    password_hash = _hash_password(password)
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (normalized_email, password_hash, ROLE_REGISTERED_USER),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with that email already exists.") from exc


def authenticate_user(email: str, password: str):
    """Return the public account fields when credentials are valid."""
    normalized_email = (email or "").strip().lower()
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, email, password_hash, role
            FROM users WHERE email = ?
            """,
            (normalized_email,),
        ).fetchone()

    if user is None or not _verify_password(password or "", user["password_hash"]):
        return None
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


def get_user_by_id(user_id: int):
    """Return account fields without exposing the stored password hash."""
    if user_id is None:
        return None
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(user) if user else None


def login_required(view):
    """Protect a view unless the session contains a valid account ID."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_user_by_id(session.get("user_id"))
        if user is None:
            session.clear()
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    """Return the currently authenticated user's public account fields."""
    return get_user_by_id(session.get("user_id"))


def assert_user_owns_record(owner_user_id) -> None:
    """Raise PermissionError unless the current account owns a record.

    Future modules must also scope database reads/updates/deletes by
    user_id in SQL; checking ownership after an unscoped query is not enough.
    """
    current_id = session.get("user_id")
    if current_id is None or str(current_id) != str(owner_user_id):
        raise PermissionError("You are not authorized to access this record.")


def new_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf_token(token: str) -> bool:
    expected = session.get("_csrf_token", "")
    return bool(expected and token and hmac.compare_digest(expected, token))
