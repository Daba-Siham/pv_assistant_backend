import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.shared.logger import get_logger


logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.request_id = request_id

        logger.info(
            f"Request started | id={request_id} | method={request.method} | path={request.url.path}"
        )

        try:
            response = await call_next(request)

        except Exception as exception:
            process_time = round((time.time() - start_time) * 1000, 2)

            logger.error(
                f"Request failed | id={request_id} | path={request.url.path} | "
                f"duration_ms={process_time} | error={str(exception)}"
            )

            raise exception

        process_time = round((time.time() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-ms"] = str(process_time)

        logger.info(
            f"Request completed | id={request_id} | status={response.status_code} | "
            f"duration_ms={process_time}"
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response