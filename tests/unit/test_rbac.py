import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.dependencies import require_admin
from app.services.auth_service import bootstrap_admins


class RbacTests(unittest.TestCase):
    def test_require_admin_rejects_non_admin_users(self):
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


if __name__ == "__main__":
    unittest.main()