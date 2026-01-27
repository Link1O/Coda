import re
import asyncio
import orjson
from colorama import Fore
from datetime import datetime, UTC
from typing import Any, Dict
from aiohttp import ClientSession
from .constants import __base_url__
from .exceptions import BadRequest, Unauthorized, Forbidden, NotFound, TooManyRequests

__status_codes__ = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
}


class Bucket:
    """
    Represents a Discord rate limit bucket for a specific route.

    Tracks the 'remaining' requests, 'limit', and the 'reset' time based on
    Discord's X-RateLimit headers.
    """

    def __init__(self):
        self.lock = asyncio.Lock()
        self.remaining = 1
        self.limit = 1
        self.reset_at = 0

    async def wait(self):
        """
        Wait until a slot is available in this bucket.
        Handles both immediate slot consumption and sleeping until reset.
        """
        async with self.lock:
            while True:
                now = datetime.now(UTC).timestamp()
                if self.remaining > 0:
                    self.remaining -= 1
                    return

                if now >= self.reset_at:
                    self.remaining = self.limit - 1
                    return

                wait_time = self.reset_at - now
                if wait_time > 0:
                    print(
                        f"Coda: {Fore.CYAN}Rate limit bucket full. Waiting {wait_time:.2f}s{Fore.RESET}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.remaining = self.limit - 1
                    return

    def update(self, headers: dict):
        """
        Update bucket state from Discord's response headers.
        """
        self.limit = int(headers.get("X-RateLimit-Limit", self.limit))
        self.remaining = int(headers.get("X-RateLimit-Remaining", 0))
        reset_after = float(headers.get("X-RateLimit-Reset-After", 0))
        self.reset_at = datetime.now(UTC).timestamp() + reset_after


class RateLimiter:
    """
    Global manager for rate limit buckets and global backoff.
    """

    def __init__(self):
        self.buckets: Dict[str, Bucket] = {}
        self.global_wait_until = 0

    async def wait_global(self):
        """
        Proactively wait if a global rate limit backoff is active.
        """
        now = datetime.now(UTC).timestamp()
        if now < self.global_wait_until:
            wait_time = self.global_wait_until - now
            print(
                f"Coda: {Fore.RED}Global backoff active. Waiting {wait_time:.2f}s{Fore.RESET}"
            )
            await asyncio.sleep(wait_time)

    def set_global_backoff(self, retry_after: float):
        """
        Set a global backoff period across all requests.
        """
        self.global_wait_until = datetime.now(UTC).timestamp() + retry_after

    def get_bucket(self, method: str, url: str) -> Bucket:
        """
        Identify and return the rate limit bucket for a specific endpoint.
        Uses regex to normalize paths (e.g., grouping all message deletions).
        """
        path = url.split(__base_url__)[-1]
        route = re.sub(r"messages/\d+", "messages/:id", path)
        route = re.sub(r"reactions/[^/]+", "reactions/:emoji", route)
        key = f"{method} {route}"

        if key not in self.buckets:
            self.buckets[key] = Bucket()
        return self.buckets[key]


_rate_limiter = RateLimiter()


async def _request(session: ClientSession, method: str, url: str, **kwargs) -> Any:
    """
    Centralized HTTP request handler for the Discord API.
    Handles proactive rate limiting, global backoffs, and error code mapping.
    """
    bucket = _rate_limiter.get_bucket(method, url)

    while True:
        await _rate_limiter.wait_global()
        await bucket.wait()

        async with session.request(method, url, **kwargs) as response:
            # Update bucket from headers
            bucket.update(response.headers)

            if response.status == 429:
                data = await response.json(loads=orjson.loads)
                retry_after = data.get("retry_after", 1)
                is_global = data.get("global", False)

                if is_global:
                    _rate_limiter.set_global_backoff(retry_after)
                    print(
                        f"Coda: {Fore.RED}GLOBAL Rate limit hit. Retrying in {retry_after}s{Fore.RESET}"
                    )
                else:
                    print(
                        f"Coda: {Fore.YELLOW}Bucket Rate limit hit ({method} {url}). Retrying in {retry_after}s{Fore.RESET}"
                    )
                    await asyncio.sleep(retry_after)
                continue

            if response.status in __status_codes__:
                raise __status_codes__[response.status](
                    f"discord API returned {response.status}"
                )

            if response.status == 204:
                return None

            try:
                return await response.json(loads=orjson.loads)
            except:
                return await response.text()
