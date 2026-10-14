import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.services.google_auth_service import verify_google_id_token


class GoogleAuthServiceTests(unittest.TestCase):
    def test_verification_requires_configured_client_id(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                verify_google_id_token("signed-token")

        self.assertEqual(raised.exception.status_code, 503)

    def test_verification_rejects_audience_for_another_client(self):
        response = _GoogleResponse({
            "email": "trader@example.com",
            "email_verified": "true",
            "sub": "google-subject",
            "aud": "another-client",
            "iss": "https://accounts.google.com",
        })
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "expected-client"}):
            with patch("app.services.google_auth_service.requests.get", return_value=response):
                with self.assertRaises(HTTPException) as raised:
                    verify_google_id_token("signed-token")

        self.assertEqual(raised.exception.status_code, 401)

    def test_verification_rejects_unverified_email_string(self):
        response = _GoogleResponse({
            "email": "trader@example.com",
            "email_verified": "false",
            "sub": "google-subject",
            "aud": "expected-client",
            "iss": "https://accounts.google.com",
        })
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "expected-client"}):
            with patch("app.services.google_auth_service.requests.get", return_value=response):
                with self.assertRaises(HTTPException) as raised:
                    verify_google_id_token("signed-token")

        self.assertEqual(raised.exception.status_code, 401)

    def test_verification_accepts_matching_verified_token(self):
        profile = {
            "email": "trader@example.com",
            "email_verified": "true",
            "sub": "google-subject",
            "aud": "expected-client",
            "iss": "https://accounts.google.com",
        }
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "expected-client"}):
            with patch("app.services.google_auth_service.requests.get", return_value=_GoogleResponse(profile)):
                self.assertEqual(verify_google_id_token("signed-token"), profile)


class _GoogleResponse:
    status_code = 200

    def __init__(self, profile):
        self.profile = profile

    def json(self):
        return self.profile


if __name__ == "__main__":
    unittest.main()