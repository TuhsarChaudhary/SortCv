# app/middleware/error_notifier.py

import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.email_utils import send_email  # SendGrid helper

class ErrorNotifierMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Notify admins of API failures."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Only trigger for production-level apps, not dev
            path = request.url.path
            error_details = traceback.format_exc()

            # You could also filter paths (e.g., skip Swagger/docs)
            try:
                send_email(
                    to_email="tusharchaudhary002350@outlook.com",  # ops email
                    subject=f"[ALERT] API failure at {path}",
                    body=f"Exception:\n{str(e)}\n\nTraceback:\n{error_details}",
                )
            except Exception:
                # Avoid infinite loops if email sending itself fails
                pass

            return Response(
                content="Internal server error. Admins have been notified.",
                status_code=500
            )
