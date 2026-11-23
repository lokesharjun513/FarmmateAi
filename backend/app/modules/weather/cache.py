# app/modules/weather/cache.py

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CacheResult(Generic[T]):
    """
    Result of a cache lookup or fetch.

    ``stale`` is True when the data was served from an expired
    cache entry because the upstream fetch failed (bounded stale
    fallback). The data itself is still the last successful
    observation.
    """

    data: T
    stale: bool = False


@dataclass(frozen=True)
class _Entry(Generic[T]):
    data: T
    fetched_at: float


class WeatherCache(Generic[T]):
    """
    In-process TTL cache:

    - ``fresh_ttl_seconds``: while an entry is this young, it is
      served directly and no upstream call is made.
    - ``max_stale_age_seconds``: beyond this age an entry is never
      served as a fallback (the caller gets the upstream error).
    - Concurrent fetches for the same key share a single in-flight
      future, so identical requests are deduplicated.
    """

    def __init__(
        self,
        *,
        fresh_ttl_seconds: float = 900.0,
        max_stale_age_seconds: float = 21600.0,
        clock: Callable[[], float] = time.time,
    ):
        self.fresh_ttl_seconds = fresh_ttl_seconds
        self.max_stale_age_seconds = max_stale_age_seconds
        self._clock = clock

        self._entries: dict[str, _Entry[T]] = {}
        self._inflight: dict[str, asyncio.Future[T]] = {}

    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[T]],
    ) -> CacheResult[T]:

        now = self._clock()
        entry = self._entries.get(key)

        if entry is not None:
            age = now - entry.fetched_at

            if age <= self.fresh_ttl_seconds:
                return CacheResult(data=entry.data)

        # A fetch for this key is already in flight; share it.
        inflight = self._inflight.get(key)

        if inflight is not None:
            return CacheResult(data=await asyncio.shield(inflight))

        task = asyncio.ensure_future(fetcher())
        self._inflight[key] = task

        try:
            data = await task
            self._entries[key] = _Entry(data=data, fetched_at=self._clock())
            return CacheResult(data=data)

        except BaseException:
            # Serve the last successful observation if it is still
            # within the bounded stale window; otherwise propagate
            # the upstream error to the caller.
            if entry is not None:
                age = self._clock() - entry.fetched_at

                if age <= self.max_stale_age_seconds:
                    return CacheResult(data=entry.data, stale=True)

            raise

        finally:
            self._inflight.pop(key, None)


def build_weather_cache_key(
    latitude: float,
    longitude: float,
) -> str:
    """
    Cache key based on rounded coordinates so requests for nearby
    points share an entry. Four decimals is roughly ~11 m of
    precision, well within weather forecast resolution.
    """
    return (
        f"{round(float(latitude), 4)}:"
        f"{round(float(longitude), 4)}"
    )


# Module-level singleton: WeatherService instances are constructed
# per request, but the cache must survive across requests.
default_weather_cache: WeatherCache = WeatherCache()
