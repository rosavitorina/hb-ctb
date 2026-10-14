import base64
import hashlib
import hmac
import os
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_SIZE = 16
_HASH_SIZE = 32
VALID_ROLES = {"admin", "user"}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_role(role: str | None) -> str:
    if role not in VALID_ROLES:
        return "user"
    return role


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_SIZE)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_HASH_SIZE,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encoded_salt}${encoded_digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, n, r, p, encoded_salt, encoded_digest = password_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError):
        return False


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_invite_code() -> str:
    return secrets.token_urlsafe(24)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_invite_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def update_user_role(email: str, role: str) -> dict | None:
    from app.infrastructure.database.auth import update_user_role as store_update_user_role

    return store_update_user_role(email, role)


def bootstrap_admins() -> list[str]:
    configured = os.getenv("INITIAL_ADMIN_EMAILS", "")
    if not configured.strip():
        return []

    emails: list[str] = []
    seen: set[str] = set()
    for raw_email in configured.split(","):
        normalized = normalize_email(raw_email)
        if not normalized or normalized in seen or "@" not in normalized:
            continue
        seen.add(normalized)
        emails.append(normalized)

    emails = emails[:3]
    for email in emails:
        update_user_role(email, "admin")
    return emails


def backfill_default_roles() -> None:
    from app.infrastructure.database.auth import backfill_user_roles

    backfill_user_roles()
