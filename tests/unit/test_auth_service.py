import unittest

from app.services.auth_service import (
    create_session_token,
    hash_session_token,
)


class AuthServiceTests(unittest.TestCase):
    def test_session_token_is_random_and_only_its_hash_is_stored(self):
        first = create_session_token()
        second = create_session_token()

        self.assertNotEqual(first, second)
        self.assertNotEqual(hash_session_token(first), first)
        self.assertEqual(hash_session_token(first), hash_session_token(first))


if __name__ == "__main__":
    unittest.main()