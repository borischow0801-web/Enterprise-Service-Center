import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.api.auth.router import router as auth_router
from app.api.enterprise.router import router as enterprise_router
from app.api.admin.router import router as admin_router
from app.api.common.router import router as common_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir_resolved, exist_ok=True)
    yield


app = FastAPI(
    title="企业服务中心系统",
    description="Enterprise Service Center API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# 开发阶段允许管理端/企业端 Vite 端口（5174 被占用时可能落到 5175）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=r"http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}:517[3-5]",
    allow_credentials=False,   # allow_credentials=True 与 allow_origins=["*"] 不兼容
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["系统"])
def health_check():
    return {"code": 0, "message": "success", "data": {"status": "ok"}, "traceId": ""}

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(enterprise_router, prefix="/api/enterprise", tags=["企业端"])
app.include_router(admin_router, prefix="/api/admin", tags=["管理端"])
app.include_router(common_router, prefix="/api/common", tags=["通用"])
