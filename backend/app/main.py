import logging
import secrets
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.auth import router as auth_router
from backend.app.api.admin.employees import router as employees_router
from backend.app.api.admin.attendance import router as attendance_router
from backend.app.api.admin.enrollment import router as enrollment_router
from backend.app.api.admin.shifts import router as shifts_router
from backend.app.api.system import router as system_router
from backend.app.api.kiosk import router as kiosk_router
from backend.app.core.config import settings
from backend.app.core.logging import configure_logging, log_extra, request_id_context


configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger("face_attendance.api")


app = FastAPI(
    title="Face Attendance API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    path = request.url.path
    is_frame = path.endswith("/frame")
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        level = logging.DEBUG if is_frame and not settings.LOG_HTTP_FRAME_REQUESTS else logging.INFO
        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING
        logger.log(
            level,
            "HTTP request completed",
            extra=log_extra(
                "http_request_completed",
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            ),
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Request validation failed",
        extra=log_extra("request_validation_failed", path=request.url.path),
    )
    safe_errors = [
        {key: value for key, value in error.items() if key != "ctx"}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Dữ liệu gửi lên không hợp lệ",
            "details": jsonable_encoder(safe_errors),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = "UNAUTHORIZED" if exc.status_code == 401 else "REQUEST_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": str(exc.detail), "details": None},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled backend exception",
        extra=log_extra(
            "unhandled_exception",
            path=request.url.path,
            exception_type=type(exc).__name__,
        ),
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Hệ thống đang gặp lỗi, vui lòng thử lại",
            "details": None,
        },
    )


app.include_router(system_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(shifts_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(enrollment_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(kiosk_router, prefix="/api")
