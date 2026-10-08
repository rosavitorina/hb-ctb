import asyncio
from collections import deque
from math import ceil
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


AUTH_LIMITS = {
    "/auth/login": (10, 60),
    "/auth/register": (5, 60 * 60),
}
MAX_TRACKED_CLIENTS = 4096


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._attempts: dict[tuple[str, str], deque[float]] = {}
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        limit = AUTH_LIMITS.get(request.url.path)
        if request.method != "POST" or limit is None:
            return await call_next(request)

        max_attempts, window_seconds = limit
        client_ip = request.client.host if request.client else "unknown"
        key = (request.url.path, client_ip)
        now = monotonic()

        async with self._lock:
            if key not in self._attempts and len(self._attempts) >= MAX_TRACKED_CLIENTS:
                for expired_key, attempts in tuple(self._attempts.items()):
                    expired_window = AUTH_LIMITS[expired_key[0]][1]
                    while attempts and now - attempts[0] >= expired_window:
                        attempts.popleft()
                    if not attempts:
                        self._attempts.pop(expired_key, None)
                if len(self._attempts) >= MAX_TRACKED_CLIENTS:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many authentication attempts; try again later"},
                        headers={"Retry-After": str(max(window for _, window in AUTH_LIMITS.values()))},
                    )

            attempts = self._attempts.setdefault(key, deque())
            while attempts and now - attempts[0] >= window_seconds:
                attempts.popleft()

            if len(attempts) >= max_attempts:
                retry_after = max(1, ceil(window_seconds - (now - attempts[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many authentication attempts; try again later"},
                    headers={"Retry-After": str(retry_after)},
                )

            attempts.append(now)

        return await call_next(request)