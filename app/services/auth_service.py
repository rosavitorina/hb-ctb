import hashlib
import os
import secrets

VALID_ROLES = {"admin", "user"}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_role(role: str | None) -> str:
    if role not in VALID_ROLES:
        return "user"
    return role


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
