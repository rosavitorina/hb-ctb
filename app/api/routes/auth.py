import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies import SESSION_COOKIE, get_current_user, require_admin
from app.domain.schemas.auth import (
    AccountResponse,
    EmailAddress,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
)
from app.infrastructure.database.auth import (
    create_invite,
    create_session,
    register_invited_user,
    delete_session,
    get_user_by_email,
    get_user_for_session,
    create_user,
    update_user_role,
)
from app.services.auth_service import (
    bootstrap_admins,
    create_invite_code,
    hash_invite_code,
    hash_password,
    create_session_token,
    hash_session_token,
    verify_password,
)
from app.services.email_service import send_invite_email, send_registration_email
from app.services.google_auth_service import verify_google_id_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
SESSION_LIFETIME = timedelta(hours=12)


@router.get("/config")
def auth_config():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip()}


def _set_session_cookie(request: Request, response: Response, token: str) -> None:
    secure_cookie = request.url.scheme == "https" or os.getenv(
        "AUTH_COOKIE_SECURE", "false"
    ).strip().lower() in {"1", "true", "yes"}
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=AccountResponse)
def login(payload: LoginRequest, request: Request, response: Response):
    try:
        user = get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email or password is incorrect")

        token = create_session_token()
        expires_at = datetime.now(timezone.utc) + SESSION_LIFETIME
        create_session(user["_id"], hash_session_token(token), expires_at)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Login failed because the auth store is unavailable")
        raise HTTPException(status_code=503, detail="Sign-in is temporarily unavailable") from exc

    _set_session_cookie(request, response, token)
    return {"id": user["id"], "email": user["email"], "role": user.get("role", "user")}


@router.post("/invite", response_model=dict)
def create_invite_for_email(payload: EmailAddress, admin_user: dict = Depends(require_admin)):
    code = create_invite_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
    try:
        create_invite(payload.email, hash_invite_code(code), expires_at)
        sent = send_invite_email(payload.email, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Invite creation failed for %s", payload.email)
        raise HTTPException(status_code=503, detail="Invite delivery is temporarily unavailable") from exc

    if not sent:
        logger.warning("Invite code was generated but not delivered to %s", payload.email)
    return {"status": "sent" if sent else "created", "email": payload.email, "role": admin_user.get("role", "admin")}


@router.get("/admin/summary")
def admin_summary(admin_user: dict = Depends(require_admin)):
    return {"status": "ok", "email": admin_user["email"], "role": admin_user.get("role", "admin")}


@router.post("/register", response_model=AccountResponse)
def register(payload: RegisterRequest, request: Request, response: Response):
    try:
        user = register_invited_user(
            payload.email,
            hash_password(payload.password),
            hash_invite_code(payload.invite_code),
        )
        token = create_session_token()
        create_session(
            user["_id"],
            hash_session_token(token),
            datetime.now(timezone.utc) + SESSION_LIFETIME,
        )
        sending = send_registration_email(user["email"])
        if not sending:
            logger.warning("Registration confirmation email was not delivered for %s", user["email"])
    except (PermissionError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invite is invalid, expired, already used, or not for this email",
        ) from exc
    except Exception as exc:
        logger.exception("Registration failed because the auth store is unavailable")
        raise HTTPException(status_code=503, detail="Account creation is temporarily unavailable") from exc

    _set_session_cookie(request, response, token)
    return {"id": user["id"], "email": user["email"], "role": user.get("role", "user")}


@router.post("/google", response_model=AccountResponse)
def google_login(payload: GoogleLoginRequest, request: Request, response: Response):
    try:
        profile = verify_google_id_token(payload.credential)
        email = profile["email"].strip().lower()
        user = get_user_by_email(email)
        if user is None:
            created = create_user(email, f"google-oauth:{profile['sub']}", role="user")
            user = created
        if profile.get("email_verified") and email.lower() in {
            configured.lower() for configured in os.getenv("INITIAL_ADMIN_EMAILS", "").split(",") if configured.strip()
        }:
            user = update_user_role(email, "admin") or user
        token = create_session_token()
        create_session(
            user["_id"],
            hash_session_token(token),
            datetime.now(timezone.utc) + SESSION_LIFETIME,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Google login failed")
        raise HTTPException(status_code=503, detail="Google sign-in is temporarily unavailable") from exc

    _set_session_cookie(request, response, token)
    return {"id": user["id"], "email": user["email"], "role": user.get("role", "user")}


@router.get("/me", response_model=AccountResponse)
def current_account(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "role": user.get("role", "user")}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        try:
            delete_session(hash_session_token(token))
        except Exception as exc:
            logger.exception("Could not delete auth session")
            raise HTTPException(status_code=503, detail="Sign-out is temporarily unavailable") from exc

    secure_cookie = request.url.scheme == "https" or os.getenv(
        "AUTH_COOKIE_SECURE", "false"
    ).strip().lower() in {"1", "true", "yes"}
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )
    return {"status": "ok"}