# Tests for the weather robustness work:
# provider bounded retries + Retry-After, credential/malformed
# handling, TTL cache freshness, concurrent deduplication, bounded
# stale-cache fallback, and the HTTP 503 surface for upstream failure.

import asyncio
import logging

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exception_handlers import register_exception_handlers
from app.modules.weather.cache import (
    WeatherCache,
    build_weather_cache_key,
)
from app.modules.weather.exceptions import (
    WeatherUpstreamRateLimitedError,
    WeatherUpstreamUnavailableError,
)
from app.modules.weather.provider import WeatherProvider
from app.modules.weather.router import router
from app.modules.weather.schemas import CurrentWeatherResponse
from app.modules.weather.service import WeatherResult


# ============================================================
# WeatherProvider: bounded retries / Retry-After / errors
# ============================================================

class FakeSleep:
    """Records asyncio.sleep calls so tests never actually wait."""

    def __init__(self, monkeypatch):
        self.sleeps = []
        monkeypatch.setattr(
            "app.modules.weather.provider.asyncio.sleep",
            self.fake_sleep,
        )

    async def fake_sleep(self, delay):
        self.sleeps.append(delay)


def valid_payload():
    return {
        "location": {"name": "Nellore", "tz_id": "Asia/Kolkata"},
        "current": {
            "temp_c": 32.5,
            "wind_kph": 12.0,
            "condition": {"code": 1000, "text": "Sunny"},
        },
        "forecast": {
            "forecastday": [{"date": "2026-11-23"}]
        },
    }


def make_provider(handler, api_key="test-key"):
    return WeatherProvider(
        transport=httpx.MockTransport(handler),
        api_key=api_key,
    )


def json_response(status_code, payload=None, headers=None):
    return httpx.Response(
        status_code,
        json=payload,
        headers=headers or {},
    )


@pytest.mark.asyncio
async def test_provider_success_builds_request(monkeypatch):
    captured = {}

    def handler(request):
        captured["params"] = dict(request.url.params)
        return json_response(200, valid_payload())

    provider = make_provider(handler)

    data = await provider.get_current_weather(14.4, 79.9)

    assert data["current"]["temp_c"] == 32.5

    # Forecast endpoint contract: days=1, aqi=no, alerts=no,
    # q=latitude,longitude, key passed as query parameter.
    assert captured["params"]["days"] == "1"
    assert captured["params"]["aqi"] == "no"
    assert captured["params"]["alerts"] == "no"
    assert captured["params"]["q"] == "14.4,79.9"
    assert captured["params"]["key"] == "test-key"


@pytest.mark.asyncio
async def test_provider_missing_key_raises_without_calling_upstream(monkeypatch):
    monkeypatch.setattr(
        "app.modules.weather.provider.settings.WEATHERAPI_API_KEY",
        None,
    )

    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return json_response(200, valid_payload())

    provider = make_provider(handler, api_key=None)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_provider_auth_rejection_not_retried(monkeypatch, status_code):
    calls = {"n": 0}
    FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        return httpx.Response(status_code)

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_provider_api_key_never_logged(monkeypatch, caplog):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(401)

    provider = make_provider(handler)

    with caplog.at_level(logging.WARNING, logger="farmmate"):
        with pytest.raises(WeatherUpstreamUnavailableError):
            await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 1
    assert "test-key" not in caplog.text


@pytest.mark.asyncio
async def test_provider_429_respects_retry_after(monkeypatch):
    calls = {"n": 0}
    fake_sleep = FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return json_response(429, headers={"Retry-After": "2"})
        return json_response(200, valid_payload())

    provider = make_provider(handler)

    await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 2
    assert fake_sleep.sleeps == [2.0]


@pytest.mark.asyncio
async def test_provider_429_without_retry_after_uses_backoff(monkeypatch):
    calls = {"n": 0}
    fake_sleep = FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        return json_response(429)

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamRateLimitedError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 2
    assert fake_sleep.sleeps == [1.0]


@pytest.mark.asyncio
async def test_provider_429_retry_after_clamped(monkeypatch):
    calls = {"n": 0}
    fake_sleep = FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            # Absurdly long Retry-After must be clamped.
            return json_response(429, headers={"Retry-After": "3600"})
        return json_response(200, valid_payload())

    provider = make_provider(handler)

    await provider.get_current_weather(14.4, 79.9)

    assert fake_sleep.sleeps == [10.0]


@pytest.mark.asyncio
async def test_provider_5xx_retries_once(monkeypatch):
    calls = {"n": 0}
    fake_sleep = FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return json_response(500)
        return json_response(200, valid_payload())

    provider = make_provider(handler)

    await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 2
    assert fake_sleep.sleeps == [1.0]


@pytest.mark.asyncio
async def test_provider_persistent_5xx_raises_unavailable(monkeypatch):
    calls = {"n": 0}
    FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        return json_response(503)

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_provider_other_4xx_not_retried(monkeypatch):
    calls = {"n": 0}
    FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        return json_response(400)

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_provider_transport_error_bounded(monkeypatch):
    calls = {"n": 0}
    fake_sleep = FakeSleep(monkeypatch)

    def handler(request):
        calls["n"] += 1
        raise httpx.ConnectError("boom")

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 2
    assert fake_sleep.sleeps == [1.0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        # Not an object at all.
        [1],
        # Missing required current fields / malformed condition.
        {"current": {}},
        {
            "current": {
                "temp_c": 30,
                "condition": {"code": 1000, "text": "Sunny"},
            }
        },
        {
            "current": {
                "temp_c": 30,
                "wind_kph": 10,
                "condition": {"code": 1000, "text": ""},
            }
        },
        {
            "current": {
                "temp_c": 30,
                "wind_kph": 10,
                "condition": {"code": "x", "text": "Sunny"},
            }
        },
        # Missing/empty forecast breakdown.
        {
            "current": {
                "temp_c": 30,
                "wind_kph": 10,
                "condition": {"code": 1000, "text": "Sunny"},
            },
            "forecast": {},
        },
        {
            "current": {
                "temp_c": 30,
                "wind_kph": 10,
                "condition": {"code": 1000, "text": "Sunny"},
            },
            "forecast": {"forecastday": []},
        },
    ],
)
async def test_provider_malformed_payloads_raise_unavailable(
    monkeypatch,
    payload,
):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return json_response(200, payload)

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_provider_non_json_body_raises_unavailable(monkeypatch):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, content=b"<html>oops</html>")

    provider = make_provider(handler)

    with pytest.raises(WeatherUpstreamUnavailableError):
        await provider.get_current_weather(14.4, 79.9)

    assert calls["n"] == 1


# ============================================================
# WeatherCache: freshness, dedup, stale fallback
# ============================================================

class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.mark.asyncio
async def test_cache_fresh_hit_skips_fetcher():
    clock = FakeClock()
    cache = WeatherCache(clock=clock)
    fetched = {"n": 0}

    async def fetcher():
        fetched["n"] += 1
        return {"temp": 1}

    first = await cache.get_or_fetch("k", fetcher)
    second = await cache.get_or_fetch("k", fetcher)

    assert first == second
    assert not first.stale
    assert fetched["n"] == 1


@pytest.mark.asyncio
async def test_cache_expired_serves_stale_bounded():
    clock = FakeClock()
    cache = WeatherCache(clock=clock, fresh_ttl_seconds=900.0)
    fetched = {"n": 0}

    async def ok_fetcher():
        fetched["n"] += 1
        return {"temp": 1}

    async def failing_fetcher():
        fetched["n"] += 1
        raise RuntimeError("upstream down")

    fresh = await cache.get_or_fetch("k", ok_fetcher)
    assert not fresh.stale

    # Just past the fresh TTL: refetch fails -> stale served.
    clock.advance(901)
    stale = await cache.get_or_fetch("k", failing_fetcher)

    assert stale.data == {"temp": 1}
    assert stale.stale is True

    # Past max stale age: the error propagates to the caller.
    clock.advance(21600)
    with pytest.raises(RuntimeError):
        await cache.get_or_fetch("k", failing_fetcher)

    assert fetched["n"] == 3


@pytest.mark.asyncio
async def test_cache_concurrent_requests_deduplicate():
    cache = WeatherCache()
    started = asyncio.Event()
    release = asyncio.Event()
    fetched = {"n": 0}

    async def slow_fetcher():
        fetched["n"] += 1
        started.set()
        await release.wait()
        return {"temp": 42}

    task_a = asyncio.create_task(
        cache.get_or_fetch("k", slow_fetcher)
    )
    task_b = asyncio.create_task(
        cache.get_or_fetch("k", slow_fetcher)
    )

    await asyncio.wait_for(started.wait(), timeout=5)
    release.set()

    results = await asyncio.gather(task_a, task_b)

    assert fetched["n"] == 1
    assert results[0] == results[1]
    assert results[0].data == {"temp": 42}


def test_cache_key_rounds_coordinates():
    assert build_weather_cache_key(14.44261, 79.98651) == (
        "14.4426:79.9865"
    )
    assert build_weather_cache_key(14.44, 79.99) == (
        "14.44:79.99"
    )


# ============================================================
# HTTP surface: 503 when upstream is unusable, stale message
# ============================================================

class MockRaisingWeatherService:
    async def get_current_weather(self, **kwargs):
        raise WeatherUpstreamRateLimitedError("rate limited")


def create_current_weather():
    return CurrentWeatherResponse(
        location="Nellore, Andhra Pradesh",
        latitude=14.4,
        longitude=79.9,
        temperature=32.5,
        feels_like=35.0,
        humidity=70,
        wind_speed=12.0,
        pressure=1008.0,
        visibility=None,
        uv_index=None,
        precipitation=0.0,
        weather_code=0,
        weather_condition="Clear Sky",
        rain_probability=20,
        sunrise="2026-08-15T05:45:00",
        sunset="2026-08-15T18:30:00",
    )


class MockStaleWeatherService:
    async def get_current_weather(self, **kwargs):
        return WeatherResult(
            data=create_current_weather(),
            stale=True,
        )


def make_app():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    return app


def test_endpoint_returns_503_when_upstream_rate_limited(monkeypatch):
    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        MockRaisingWeatherService,
    )

    client = TestClient(make_app())

    response = client.get(
        "/weather/current",
        params={"latitude": 14.4, "longitude": 79.9},
    )

    assert response.status_code == 503

    body = response.json()

    assert body["success"] is False
    assert "temporarily unavailable" in body["message"]
    assert body["errors"] == []


def test_endpoint_stale_message(monkeypatch):
    monkeypatch.setattr(
        "app.modules.weather.router.WeatherService",
        MockStaleWeatherService,
    )

    client = TestClient(make_app())

    response = client.get(
        "/weather/current",
        params={"latitude": 14.4, "longitude": 79.9},
    )

    assert response.status_code == 200
    assert "last available weather data" in response.json()["message"]
