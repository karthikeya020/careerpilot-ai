"""Redis-backed fixed-window rate limiting for brute-force and
account-enumeration protection on sensitive endpoints (login, register).

Fails open (logs a warning, allows the request) if Redis is unreachable --
the same graceful-degradation posture GraphRAG and the AI provider layer
already take elsewhere in this codebase (Constitution rule 13:
demo-critical features need a deterministic fallback, and authentication
staying reachable outweighs rate limiting when the limiter's own dependency
is down).

Each named limiter is a stable, importable object (not a fresh closure per
request) specifically so tests can override it via
`app.dependency_overrides[login_rate_limiter] = lambda: None` the same way
`get_db` is already overridden -- real IP-keyed limits would otherwise
throttle the test suite itself, which registers/logs in far more than 10
times a minute from the same TestClient "IP".
"""

import logging

from fastapi import Request

from app.core.errors import AppError
from app.core.redis_client import get_redis

logger = logging.getLogger("careerpilot")


class RateLimitedError(AppError):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            "Too many requests. Please wait before trying again.",
            status_code=429,
            code="rate_limited",
            details={"retry_after_seconds": retry_after_seconds},
        )


class RateLimiter:
    def __init__(self, key_prefix: str, max_requests: int, window_seconds: int) -> None:
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{self.key_prefix}:{client_ip}"
        try:
            client = get_redis()
            count = client.incr(key)
            if count == 1:
                client.expire(key, self.window_seconds)
            if count > self.max_requests:
                ttl = client.ttl(key)
                raise RateLimitedError(retry_after_seconds=ttl if ttl and ttl > 0 else self.window_seconds)
        except RateLimitedError:
            raise
        except Exception:
            logger.warning("Rate limiter unavailable for %s -- failing open", self.key_prefix)


# One shared window per sensitive endpoint. 10 attempts/minute per IP is
# generous enough for a legitimate user who mistyped a password twice, tight
# enough to slow down credential stuffing / registration-enumeration bots.
login_rate_limiter = RateLimiter("login", max_requests=10, window_seconds=60)
register_rate_limiter = RateLimiter("register", max_requests=10, window_seconds=60)
