import time
import uuid
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.exceptions import BaseAppException
from app.core.logging import logger, request_id_var, session_id_var, user_id_var


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_token = request_id_var.set(request_id)

        # Clear other context tokens for safety on each request
        session_id_token = session_id_var.set(request.headers.get("X-Session-ID") or "")
        user_id_token = user_id_var.set("")  # Set later in Auth middleware/dependency

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            logger.info(
                "Request processed successfully",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "duration_seconds": round(process_time, 4),
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response

        except BaseAppException as exc:
            process_time = time.perf_counter() - start_time
            logger.warning(
                f"Application exception caught: {exc.message}",
                extra={
                    "status_code": exc.status_code,
                    "duration_seconds": round(process_time, 4),
                    "detail": exc.detail,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": exc.message, "detail": exc.detail, "success": False},
            )

        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.exception(
                "Unhandled system exception in request pipeline",
                extra={
                    "duration_seconds": round(process_time, 4),
                },
            )
            return JSONResponse(
                status_code=500,
                content={
                    "message": "An unexpected error occurred. Please contact support.",
                    "detail": str(exc),
                    "success": False,
                },
            )

        finally:
            # Reset ContextVars
            request_id_var.reset(request_id_token)
            session_id_var.reset(session_id_token)
            user_id_var.reset(user_id_token)
