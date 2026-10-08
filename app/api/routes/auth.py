import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies import SESSION_COOKIE, get_current_user
from app.domain.schemas.auth import AccountResponse, LoginRequest, RegisterRequest
from app.infrastructure.database.auth import (
    create_session,
    register_invited_user,
    delete_session,
    get_user_by_email,
    get_user_for_session,
)
from app.services.auth_service import (
    hash_invite_code,
    hash_password,
    create_session_token,
    hash_session_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
SESSION_LIFETIME = timedelta(hours=12)


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
    return {"id": user["id"], "email": user["email"]}


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
    except (PermissionError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invite is invalid, expired, already used, or not for this email",
        ) from exc
    except Exception as exc:
        logger.exception("Registration failed because the auth store is unavailable")
        raise HTTPException(status_code=503, detail="Account creation is temporarily unavailable") from exc

    _set_session_cookie(request, response, token)
    return {"id": user["id"], "email": user["email"]}


@router.get("/me", response_model=AccountResponse)
def current_account(user: dict = Depends(get_current_user)):
    return user


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