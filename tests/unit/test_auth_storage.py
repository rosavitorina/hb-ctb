import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.infrastructure.database.auth import (
    create_google_user,
    get_user_by_email,
)


class AuthStorageTests(unittest.TestCase):
    def test_new_user_retains_mongo_id_for_session_creation(self):
        user_id = ObjectId("507f1f77bcf86cd799439011")
        users = MagicMock()
        users.insert_one.return_value.inserted_id = user_id
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock())

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            account = create_google_user("Trader@Example.com", "google-subject", role="user")

        self.assertEqual(account["_id"], user_id)
        self.assertEqual(account["id"], str(user_id))
        self.assertEqual(account["email"], "trader@example.com")
        self.assertEqual(users.insert_one.call_args.args[0]["google_subject"], "google-subject")

    def test_user_lookup_keeps_mongo_id_for_session_creation(self):
        user_id = ObjectId("507f1f77bcf86cd799439011")
        stored_user = {
            "_id": user_id,
            "email": "trader@example.com",
            "google_subject": "google-subject",
        }
        users = MagicMock()
        users.find_one.return_value = stored_user
        collections = MagicMock()
        collections.__enter__.return_value = (users, MagicMock())

        with patch(
            "app.infrastructure.database.auth._auth_collections",
            return_value=collections,
        ):
            user = get_user_by_email(" Trader@Example.com ")

        users.find_one.assert_called_once_with({"email": "trader@example.com"})
        self.assertEqual(user["_id"], user_id)
        self.assertEqual(user["id"], str(user_id))


if __name__ == "__main__":
    unittest.main()