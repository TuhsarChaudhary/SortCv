import time
import logging
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Setup logger
logger = logging.getLogger("response_time_logger")
logger.setLevel(logging.INFO)

# Ensure logs directory exists before creating handler
os.makedirs("logs", exist_ok=True)
# Log file path
file_handler = logging.FileHandler("logs/response_times.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Avoid adding multiple handlers in reload mode
if not logger.handlers:
    logger.addHandler(file_handler)


class LogResponseTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Log response times."""
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000  # ms
        method = request.method
        path = request.url.path
        status = response.status_code

        log_message = f"{method} {path} returned {status} in {duration:.2f} ms"
        logger.info(log_message)

        return response
