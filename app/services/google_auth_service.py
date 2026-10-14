import os
from datetime import datetime, timezone

import requests
from fastapi import HTTPException

GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


def verify_google_id_token(token: str) -> dict:
    if not token or not token.strip():
        raise HTTPException(status_code=401, detail="A valid Google credential is required.")

    configured_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not configured_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured for this app.")

    try:
        response = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="Google sign-in is temporarily unavailable") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="The Google credential could not be validated.")

    profile = response.json()
    if not profile.get("email") or not profile.get("sub"):
        raise HTTPException(status_code=401, detail="Google account email is required.")
    if str(profile.get("email_verified", "")).lower() != "true":
        raise HTTPException(status_code=401, detail="Google account email must be verified.")

    if profile.get("aud") != configured_client_id:
        raise HTTPException(status_code=401, detail="Google client ID did not match this app.")

    if profile.get("iss") not in GOOGLE_ISSUERS:
        raise HTTPException(status_code=401, detail="Google token issuer is not trusted.")

    exp = profile.get("exp")
    if exp is not None:
        now_epoch = datetime.now(timezone.utc).timestamp()
        if int(exp) < int(now_epoch):
            raise HTTPException(status_code=401, detail="Google credential has expired.")

    return profile
