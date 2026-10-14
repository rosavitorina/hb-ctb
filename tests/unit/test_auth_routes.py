import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from starlette.responses import Response

from app.api.dependencies import SESSION_COOKIE, get_current_user
from app.api.routes.auth import auth_config, google_login, logout


class AuthRouteTests(unittest.TestCase):
    def test_auth_config_exposes_google_client_id(self):
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "client-id"}):
            self.assertEqual(auth_config(), {"google_client_id": "client-id"})

    def test_google_login_creates_or_reuses_account_and_sets_session_cookie(self):
        payload = SimpleNamespace(credential="google-credential")
        request = SimpleNamespace(url=SimpleNamespace(scheme="https"), cookies={})
        response = Response()
        user = {"_id": "database-user-id", "id": "database-user-id", "email": "trader@example.com", "role": "user"}

        with patch(
            "app.api.routes.auth.verify_google_id_token",
            return_value={"email": "Trader@Example.com", "sub": "google-subject", "email_verified": True},
        ):
            with patch("app.api.routes.auth.get_user_by_email", return_value=None):
                with patch("app.api.routes.auth.create_google_user", return_value=user) as create_user:
                    with patch("app.api.routes.auth.create_session_token", return_value="raw-token"):
                        with patch("app.api.routes.auth.hash_session_token", return_value="session-hash"):
                            with patch("app.api.routes.auth.create_session") as create_session:
                                result = google_login(payload, request, response)

        self.assertEqual(result, {"id": "database-user-id", "email": "trader@example.com", "role": "user"})
        create_user.assert_called_once_with("trader@example.com", "google-subject", role="user")
        create_session.assert_called_once()
        self.assertEqual(create_session.call_args.args[1], "session-hash")
        self.assertIn(f"{SESSION_COOKIE}=raw-token", response.headers["set-cookie"])

    def test_google_admin_promotion_keeps_mongo_id_for_session(self):
        payload = SimpleNamespace(credential="google-credential")
        request = SimpleNamespace(url=SimpleNamespace(scheme="https"), cookies={})
        response = Response()
        user = {"_id": "mongo-user-id", "id": "mongo-user-id", "email": "admin@example.com", "role": "user"}

        with patch.dict("os.environ", {"INITIAL_ADMIN_EMAILS": "admin@example.com"}):
            with patch(
                "app.api.routes.auth.verify_google_id_token",
                return_value={"email": "admin@example.com", "sub": "google-subject", "email_verified": True},
            ):
                with patch("app.api.routes.auth.get_user_by_email", return_value=user):
                    with patch("app.api.routes.auth.update_user_role", return_value={
                        "id": "mongo-user-id",
                        "email": "admin@example.com",
                        "role": "admin",
                    }):
                        with patch("app.api.routes.auth.create_session_token", return_value="raw-token"):
                            with patch("app.api.routes.auth.hash_session_token", return_value="session-hash"):
                                with patch("app.api.routes.auth.create_session") as create_session:
                                    result = google_login(payload, request, response)

        self.assertEqual(result, {"id": "mongo-user-id", "email": "admin@example.com", "role": "admin"})
        self.assertEqual(create_session.call_args.args[0], "mongo-user-id")

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