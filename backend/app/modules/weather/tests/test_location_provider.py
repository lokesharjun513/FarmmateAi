import httpx
import pytest

from app.modules.weather.location_provider import LocationProvider


class MockResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class MockClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.url = None
        self.params = None
        self.headers = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url, params, headers):
        self.url = url
        self.params = params
        self.headers = headers

        if self.error:
            raise self.error

        return self.response


@pytest.mark.asyncio
async def test_get_location_name_success(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "village": "Vasili",
                "county": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Vasili, Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_prefers_village(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "village": "Vasili",
                "town": "Nellore",
                "city": "Nellore",
                "municipality": "Nellore Municipality",
                "county": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Vasili, Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_uses_town(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "town": "Nellore",
                "county": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_uses_city(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "city": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_uses_municipality(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "municipality": "Nellore Municipality",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Nellore Municipality, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_uses_county(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "county": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_uses_state_district(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "village": "Vasili",
                "state_district": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Vasili, Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_does_not_duplicate_district(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "village": "Nellore",
                "county": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Nellore, Andhra Pradesh"


@pytest.mark.asyncio
async def test_get_location_name_does_not_duplicate_state(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "village": "Vasili",
                "county": "Nellore",
                "state": "Vasili",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Vasili, Nellore"


@pytest.mark.asyncio
async def test_get_location_name_display_name_fallback(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {},
            "display_name": (
                "Vasili, Nellore, Andhra Pradesh, India"
            ),
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Vasili"


@pytest.mark.asyncio
async def test_get_location_name_returns_current_location_when_address_missing(
    monkeypatch,
):
    response = MockResponse({})

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Current Location"


@pytest.mark.asyncio
async def test_get_location_name_returns_current_location_when_address_empty(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {},
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Current Location"


@pytest.mark.asyncio
async def test_get_location_name_http_error(
    monkeypatch,
):
    client = MockClient(
        error=httpx.HTTPError("Request failed")
    )

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    result = await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert result == "Current Location"


@pytest.mark.asyncio
async def test_get_location_name_sends_correct_request(
    monkeypatch,
):
    response = MockResponse(
        {
            "address": {
                "city": "Nellore",
                "state": "Andhra Pradesh",
            }
        }
    )

    client = MockClient(response=response)

    monkeypatch.setattr(
        "app.modules.weather.location_provider.httpx.AsyncClient",
        lambda timeout: client,
    )

    provider = LocationProvider()

    await provider.get_location_name(
        latitude=14.4426,
        longitude=79.9865,
    )

    assert client.url == LocationProvider.BASE_URL

    assert client.params == {
        "lat": 14.4426,
        "lon": 79.9865,
        "format": "jsonv2",
        "zoom": 10,
        "addressdetails": 1,
    }

    assert client.headers == {
        "User-Agent": "FarmMateAI/1.0",
    }


def test_location_provider_base_url():
    provider = LocationProvider()

    assert provider.BASE_URL == (
        "https://nominatim.openstreetmap.org/reverse"
    )