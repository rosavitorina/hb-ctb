from fastapi import HTTPException, Request

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
	return user
