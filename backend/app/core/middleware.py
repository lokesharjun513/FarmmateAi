import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        request_id = str(uuid.uuid4())

        start = time.perf_counter()

        logger.info(
            "[%s] %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        try:

            response = await call_next(request)

        except Exception:

            duration = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            logger.exception(
                "[%s] %s %s FAILED (%sms)",
                request_id,
                request.method,
                request.url.path,
                duration,
            )

            raise

        duration = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        logger.info(
            "[%s] %s %s %s (%sms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        response.headers["X-Request-ID"] = request_id

        return response