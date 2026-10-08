import asyncio
import unittest

from fastapi import Request, Response

from app.api.middleware.auth_rate_limit import AuthRateLimitMiddleware


class AuthRateLimitTests(unittest.TestCase):
    def test_login_attempts_are_limited_per_client(self):
        middleware = AuthRateLimitMiddleware(lambda scope, receive, send: None)
        request = Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/auth/login",
                "raw_path": b"/auth/login",
                "query_string": b"",
                "headers": [],
                "client": ("192.0.2.10", 45000),
                "server": ("localhost", 8000),
            }
        )

        async def verify_limit():
            async def continue_request(_request):
                return Response(status_code=200)

            responses = [
                await middleware.dispatch(request, continue_request)
                for _ in range(11)
            ]
            return responses

        responses = asyncio.run(verify_limit())

        self.assertTrue(all(response.status_code == 200 for response in responses[:10]))
        self.assertEqual(responses[10].status_code, 429)
        self.assertIn("Retry-After", responses[10].headers)


if __name__ == "__main__":
    unittest.main()