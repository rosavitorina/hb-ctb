import os
from contextlib import contextmanager
from datetime import datetime, timezone

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


@contextmanager
def _auth_collections():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI must be set in the environment or .env file")

    client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())
    try:
        database = client["integracao_db"]
        yield database["users"], database["sessions"], database["invites"]
    finally:
        client.close()


def create_user(email: str, password_hash: str) -> dict:
    try:
        with _auth_collections() as (users, _, _):
            users.create_index("email", unique=True)
            result = users.insert_one(
                {
                    "email": email.strip().lower(),
                    "password_hash": password_hash,
                    "created_at": datetime.now(timezone.utc),
                }
            )
    except DuplicateKeyError as exc:
        raise ValueError("An account with that email already exists") from exc

    return {"id": str(result.inserted_id), "email": email.strip().lower()}


def get_user_by_email(email: str) -> dict | None:
    with _auth_collections() as (users, _, _):
        user = users.find_one({"email": email.strip().lower()})

    if user is None:
        return None
    user["id"] = str(user["_id"])
    return user


def update_user_password(email: str, password_hash: str) -> dict | None:
    normalized_email = email.strip().lower()
    with _auth_collections() as (users, sessions, _):
        user = users.find_one({"email": normalized_email}, {"_id": 1})
        if user is None:
            return None

        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        sessions.delete_many({"user_id": user["_id"]})

    return {"id": str(user["_id"]), "email": normalized_email}


def create_invite(email: str, code_hash: str, expires_at: datetime) -> None:
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)
    with _auth_collections() as (users, _, invites):
        if users.find_one({"email": normalized_email}, {"_id": 1}):
            raise ValueError("An account with that email already exists")
        invites.create_index("email", unique=True)
        invites.create_index("expires_at", expireAfterSeconds=0)
        invites.update_one(
            {"email": normalized_email},
            {
                "$set": {
                    "code_hash": code_hash,
                    "expires_at": expires_at,
                    "created_at": now,
                }
            },
            upsert=True,
        )


def register_invited_user(
    email: str,
    password_hash: str,
    invite_code_hash: str,
) -> dict:
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)
    try:
        with _auth_collections() as (users, _, invites):
            users.create_index("email", unique=True)
            if users.find_one({"email": normalized_email}, {"_id": 1}):
                raise ValueError("An account with that email already exists")

            invite = invites.find_one_and_delete(
                {
                    "email": normalized_email,
                    "code_hash": invite_code_hash,
                    "expires_at": {"$gt": now},
                }
            )
            if invite is None:
                raise PermissionError("Invite is invalid, expired, or already used")

            result = users.insert_one(
                {
                    "email": normalized_email,
                    "password_hash": password_hash,
                    "created_at": now,
                }
            )
    except DuplicateKeyError as exc:
        raise ValueError("An account with that email already exists") from exc

    return {
        "_id": result.inserted_id,
        "id": str(result.inserted_id),
        "email": normalized_email,
    }


def create_session(user_id, token_hash: str, expires_at: datetime) -> None:
    with _auth_collections() as (_, sessions, _):
        sessions.create_index("token_hash", unique=True)
        sessions.create_index("expires_at", expireAfterSeconds=0)
        sessions.insert_one(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
            }
        )


def get_user_for_session(token_hash: str) -> dict | None:
    now = datetime.now(timezone.utc)
    with _auth_collections() as (users, sessions, _):
        session = sessions.find_one(
            {"token_hash": token_hash, "expires_at": {"$gt": now}}
        )
        if session is None:
            return None
        user = users.find_one({"_id": session["user_id"]})

    if user is None:
        return None
    user_id = str(user.pop("_id"))
    return {"id": user_id, "email": user["email"]}


def delete_session(token_hash: str) -> None:
    with _auth_collections() as (_, sessions, _):
        sessions.delete_one({"token_hash": token_hash})