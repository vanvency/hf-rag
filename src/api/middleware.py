import time
from typing import Callable

from fastapi import Request, Response


class LoggingMiddleware:
    def __init__(self, logger):
        self.logger = logger

    async def __call__(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        self.logger.info(
            "%s %s - %sms %s",
            request.method,
            request.url.path,
            round(elapsed, 2),
            response.status_code,
        )
        return response

