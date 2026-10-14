from fastapi import Depends, HTTPException, Request

from app.infrastructure.database.auth import get_user_for_session
from app.services.auth_service import hash_session_token

SESSION_COOKIE = "hb_session"


def get_current_user(request: Request) -> dict:
	token = request.cookies.get(SESSION_COOKIE)
	if not token:
		raise HTTPException(status_code=401, detail="Sign-in required")

	user = get_user_for_session(hash_session_token(token))
	if user is None:
		raise HTTPException(status_code=401, detail="Session expired; sign in again")
	if user.get("role") not in {"admin", "user"}:
		user["role"] = "user"
	return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
	if user.get("role") != "admin":
		raise HTTPException(status_code=403, detail="Administrator access required")
	return user
