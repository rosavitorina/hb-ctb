import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.infrastructure.database.auth import (
    create_invite,
    get_user_by_email,
    register_invited_user,
    update_user_password,
)


class AuthStorageTests(unittest.TestCase):
    def test_user_lookup_keeps_mongo_id_for_session_creation(self):
        user_id = ObjectId("507f1f77bcf86cd799439011")
        stored_user = {
            "_id": user_id,
            "email": "trader@example.com",
            "password_hash": "stored-hash",
        }
        users = MagicMock()
        users.find_one.return_value = stored_user
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock(), MagicMock())

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            user = get_user_by_email(" Trader@Example.com ")

        users.find_one.assert_called_once_with({"email": "trader@example.com"})
        self.assertEqual(user["_id"], user_id)
        self.assertEqual(user["id"], str(user_id))
        self.assertEqual(user["password_hash"], "stored-hash")

    def test_password_update_revokes_sessions_for_the_user(self):
        user_id = ObjectId("507f1f77bcf86cd799439011")
        users = MagicMock()
        users.find_one.return_value = {"_id": user_id}
        sessions = MagicMock()
        collections = MagicMock()
        collections.__enter__.return_value = (users, sessions, MagicMock())

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            account = update_user_password(" Trader@Example.com ", "new-hash")

        users.update_one.assert_called_once()
        self.assertEqual(users.update_one.call_args.args[0], {"_id": user_id})
        self.assertEqual(
            users.update_one.call_args.args[1]["$set"]["password_hash"],
            "new-hash",
        )
        sessions.delete_many.assert_called_once_with({"user_id": user_id})
        self.assertEqual(account, {"id": str(user_id), "email": "trader@example.com"})

    def test_creates_or_replaces_invite_for_normalized_email(self):
        users = MagicMock()
        users.find_one.return_value = None
        invites = MagicMock()
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock(), invites)

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            create_invite(" Trader@Example.com ", "code-hash", datetime.now(timezone.utc))

        invites.create_index.assert_any_call("email", unique=True)
        invites.create_index.assert_any_call("expires_at", expireAfterSeconds=0)
        self.assertEqual(invites.update_one.call_args.args[0], {"email": "trader@example.com"})
        self.assertEqual(invites.update_one.call_args.args[1]["$set"]["code_hash"], "code-hash")
        self.assertTrue(invites.update_one.call_args.kwargs["upsert"])

    def test_registration_consumes_matching_invite_and_creates_account(self):
        user_id = ObjectId("507f1f77bcf86cd799439011")
        users = MagicMock()
        users.find_one.return_value = None
        users.insert_one.return_value.inserted_id = user_id
        invites = MagicMock()
        invites.find_one_and_delete.return_value = {"email": "trader@example.com"}
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock(), invites)

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            account = register_invited_user(
                " Trader@Example.com ",
                "stored-password-hash",
                "invite-hash",
            )

        invites.find_one_and_delete.assert_called_once()
        query = invites.find_one_and_delete.call_args.args[0]
        self.assertEqual(query["email"], "trader@example.com")
        self.assertEqual(query["code_hash"], "invite-hash")
        self.assertIn("$gt", query["expires_at"])
        self.assertEqual(users.insert_one.call_args.args[0]["password_hash"], "stored-password-hash")
        self.assertEqual(account["_id"], user_id)

    def test_registration_rejects_invalid_invite_without_creating_user(self):
        users = MagicMock()
        users.find_one.return_value = None
        invites = MagicMock()
        invites.find_one_and_delete.return_value = None
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock(), invites)

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            with self.assertRaisesRegex(PermissionError, "invalid, expired, or already used"):
                register_invited_user("trader@example.com", "stored-hash", "wrong-hash")

        users.insert_one.assert_not_called()

    def test_existing_account_does_not_consume_invite(self):
        users = MagicMock()
        users.find_one.return_value = {"_id": ObjectId("507f1f77bcf86cd799439011")}
        invites = MagicMock()
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock(), invites)

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            with self.assertRaisesRegex(ValueError, "already exists"):
                register_invited_user("trader@example.com", "stored-hash", "invite-hash")

        invites.find_one_and_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()