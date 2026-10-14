import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from starlette.responses import Response

from app.api.dependencies import require_admin
from app.api.routes.auth import register
from app.domain.schemas.auth import RegisterRequest
from app.services.auth_service import bootstrap_admins
from app.services.email_service import send_invite_email, send_registration_email


class RbacAndEmailTests(unittest.TestCase):
    def test_register_assigns_default_user_role(self):
        payload = RegisterRequest(
            email="trader@example.com",
            password="a-strong-registration-password",
            invite_code="A" * 32,
        )
        request = SimpleNamespace(url=SimpleNamespace(scheme="https"), cookies={})
        response = Response()
        user = {"_id": "database-user-id", "id": "database-user-id", "email": "trader@example.com", "role": "user"}

        with patch("app.api.routes.auth.hash_password", return_value="password-hash"):
            with patch("app.api.routes.auth.hash_invite_code", return_value="invite-hash"):
                with patch("app.api.routes.auth.register_invited_user", return_value=user) as create_user:
                    with patch("app.api.routes.auth.create_session_token", return_value="raw-token"):
                        with patch("app.api.routes.auth.hash_session_token", return_value="session-hash"):
                            with patch("app.api.routes.auth.create_session"):
                                with patch("app.api.routes.auth.send_registration_email", return_value=True):
                                    result = register(payload, request, response)

        self.assertEqual(result["role"], "user")
        self.assertEqual(create_user.call_args.args[0], "trader@example.com")

    def test_require_admin_rejects_non_admin_users(self):
        request = SimpleNamespace(cookies={})
        user = {"id": "user-123", "email": "user@example.com", "role": "user"}

        with self.assertRaises(HTTPException) as raised:
            require_admin(user=user)

        self.assertEqual(raised.exception.status_code, 403)

    def test_bootstrap_admins_promotes_only_configured_emails(self):
        with patch.dict(os.environ, {"INITIAL_ADMIN_EMAILS": "Admin@Example.com, second@example.com"}, clear=False):
            with patch("app.services.auth_service.update_user_role") as update_user_role:
                bootstrap_admins()

        self.assertEqual(update_user_role.call_count, 2)
        emails = [call.args[0] for call in update_user_role.call_args_list]
        self.assertEqual(emails, ["admin@example.com", "second@example.com"])

    def test_email_helpers_use_transport(self):
        with patch("app.services.email_service.send_email") as send_email:
            send_invite_email("invite@example.com", "SECRET-CODE")
            send_registration_email("welcome@example.com")

        self.assertEqual(send_email.call_count, 2)


if __name__ == "__main__":
    unittest.main()
