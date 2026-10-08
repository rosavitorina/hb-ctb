import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from starlette.responses import Response

from app.api.dependencies import SESSION_COOKIE, get_current_user
from app.api.routes.auth import login, logout, register
from app.domain.schemas.auth import LoginRequest, RegisterRequest


class AuthRouteTests(unittest.TestCase):
    def test_login_sets_http_only_session_cookie_and_stores_token_hash(self):
        account = LoginRequest(email="Trader@Example.com", password="long-enough-password")
        user = {
            "_id": "database-user-id",
            "id": "database-user-id",
            "email": "trader@example.com",
            "password_hash": "stored-password-hash",
        }
        request = SimpleNamespace(url=SimpleNamespace(scheme="https"), cookies={})
        response = Response()

        with patch("app.api.routes.auth.get_user_by_email", return_value=user):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch("app.api.routes.auth.create_session_token", return_value="raw-token"):
                    with patch("app.api.routes.auth.hash_session_token", return_value="token-hash"):
                        with patch("app.api.routes.auth.create_session") as create_session:
                            result = login(account, request, response)

        cookie = response.headers["set-cookie"]
        self.assertEqual(result, {"id": "database-user-id", "email": "trader@example.com"})
        self.assertIn(f"{SESSION_COOKIE}=raw-token", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        create_session.assert_called_once()
        self.assertEqual(create_session.call_args.args[1], "token-hash")

    def test_login_does_not_create_a_session_for_invalid_credentials(self):
        account = LoginRequest(email="trader@example.com", password="long-enough-password")
        request = SimpleNamespace(url=SimpleNamespace(scheme="http"), cookies={})

        with patch("app.api.routes.auth.get_user_by_email", return_value=None):
            with patch("app.api.routes.auth.create_session") as create_session:
                with self.assertRaises(HTTPException) as raised:
                    login(account, request, Response())

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.detail, "Email or password is incorrect")
        create_session.assert_not_called()

    def test_registration_creates_account_and_sets_session_cookie(self):
        payload = RegisterRequest(
            email="Trader@Example.com",
            password="a-strong-registration-password",
            invite_code="A" * 32,
        )
        user = {
            "_id": "database-user-id",
            "id": "database-user-id",
            "email": "trader@example.com",
        }
        request = SimpleNamespace(url=SimpleNamespace(scheme="https"), cookies={})
        response = Response()

        with patch("app.api.routes.auth.hash_password", return_value="password-hash"):
            with patch("app.api.routes.auth.hash_invite_code", return_value="invite-hash"):
                with patch("app.api.routes.auth.register_invited_user", return_value=user) as create_user:
                    with patch("app.api.routes.auth.create_session_token", return_value="raw-token"):
                        with patch("app.api.routes.auth.hash_session_token", return_value="session-hash"):
                            with patch("app.api.routes.auth.create_session") as create_session:
                                result = register(payload, request, response)

        self.assertEqual(result, {"id": "database-user-id", "email": "trader@example.com"})
        create_user.assert_called_once_with("trader@example.com", "password-hash", "invite-hash")
        create_session.assert_called_once()
        self.assertEqual(create_session.call_args.args[1], "session-hash")
        self.assertIn(f"{SESSION_COOKIE}=raw-token", response.headers["set-cookie"])
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("Secure", response.headers["set-cookie"])

    def test_registration_rejects_invalid_invite(self):
        payload = RegisterRequest(
            email="trader@example.com",
            password="a-strong-registration-password",
            invite_code="A" * 32,
        )
        request = SimpleNamespace(url=SimpleNamespace(scheme="http"), cookies={})

        with patch(
            "app.api.routes.auth.register_invited_user",
            side_effect=PermissionError("invalid invite"),
        ):
            with patch("app.api.routes.auth.create_session") as create_session:
                with self.assertRaises(HTTPException) as raised:
                    register(payload, request, Response())

        self.assertEqual(raised.exception.status_code, 400)
        create_session.assert_not_called()

    def test_current_user_requires_a_session_cookie(self):
        request = SimpleNamespace(cookies={})

        with self.assertRaises(HTTPException) as raised:
            get_current_user(request)

        self.assertEqual(raised.exception.status_code, 401)

    def test_current_user_resolves_a_valid_session(self):
        request = SimpleNamespace(cookies={SESSION_COOKIE: "raw-token"})
        account = {"id": "database-user-id", "email": "trader@example.com"}

        with patch(
            "app.api.dependencies.hash_session_token",
            return_value="token-hash",
        ) as hash_token:
            with patch(
                "app.api.dependencies.get_user_for_session",
                return_value=account,
            ) as get_session_user:
                result = get_current_user(request)

        self.assertEqual(result, account)
        hash_token.assert_called_once_with("raw-token")
        get_session_user.assert_called_once_with("token-hash")

    def test_logout_revokes_cookie_session(self):
        request = SimpleNamespace(
            cookies={SESSION_COOKIE: "raw-token"},
            url=SimpleNamespace(scheme="http"),
        )
        response = Response()

        with patch("app.api.routes.auth.hash_session_token", return_value="token-hash"):
            with patch("app.api.routes.auth.delete_session") as delete_session:
                result = logout(request, response)

        self.assertEqual(result, {"status": "ok"})
        delete_session.assert_called_once_with("token-hash")
        self.assertIn(f"{SESSION_COOKIE}=", response.headers["set-cookie"])
        self.assertIn("HttpOnly", response.headers["set-cookie"])


if __name__ == "__main__":
    unittest.main()