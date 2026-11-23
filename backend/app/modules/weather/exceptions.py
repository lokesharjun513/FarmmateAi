# app/modules/weather/exceptions.py

from app.shared.exceptions import WeatherServiceError


class WeatherUpstreamRateLimitedError(WeatherServiceError):
    """
    Raised when the upstream weather provider replies with HTTP 429
    (Too Many Requests) after bounded retries.
    """

    pass


class WeatherUpstreamUnavailableError(WeatherServiceError):
    """
    Raised when the upstream weather provider is unavailable
    (network failure, 5xx, or an unexpected provider response)
    after bounded retries.
    """

    pass
