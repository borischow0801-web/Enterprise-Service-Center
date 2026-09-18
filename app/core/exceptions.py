"""
Business error codes and exception classes.

All business exceptions inherit from AppException.
The global handler converts them to the unified JSON response format.
"""

import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ── Error Code Registry ──────────────────────────────────────────────────────

class ErrorCode:
    SUCCESS = 0

    # 4xx – client errors
    PARAM_INVALID = 40001          # 参数校验失败
    NOT_LOGGED_IN = 40101          # 未登录
    LOGIN_FAILED = 40102           # 账号或密码错误
    FORBIDDEN = 40301              # 无权限
    NOT_FOUND = 40401              # 数据不存在
    STATUS_NOT_ALLOWED = 40901     # 状态不允许当前操作
    MEETING_ROOM_CONFLICT = 40902  # 会议室预约时间冲突
    ENTERPRISE_RESTRICTED = 40903  # 企业已被限制预约会议室
    ALREADY_REGISTERED = 40904     # 该企业已注册

    # 5xx – server errors
    SYSTEM_ERROR = 50001           # 系统异常
    THIRD_PARTY_AUTH_ERROR = 50002 # 第三方认证接口异常
    FILE_UPLOAD_FAILED = 50003     # 文件上传失败


_ERROR_MESSAGES: dict[int, str] = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.PARAM_INVALID: "参数校验失败",
    ErrorCode.NOT_LOGGED_IN: "未登录",
    ErrorCode.LOGIN_FAILED: "账号或密码错误",
    ErrorCode.FORBIDDEN: "无权限",
    ErrorCode.NOT_FOUND: "数据不存在",
    ErrorCode.STATUS_NOT_ALLOWED: "状态不允许当前操作",
    ErrorCode.MEETING_ROOM_CONFLICT: "会议室预约时间冲突",
    ErrorCode.ENTERPRISE_RESTRICTED: "企业已被限制预约会议室",
    ErrorCode.ALREADY_REGISTERED: "该企业已注册，请直接登录",
    ErrorCode.SYSTEM_ERROR: "系统异常",
    ErrorCode.THIRD_PARTY_AUTH_ERROR: "第三方认证接口异常",
    ErrorCode.FILE_UPLOAD_FAILED: "文件上传失败",
}


# ── Exception Classes ─────────────────────────────────────────────────────────

class AppException(Exception):
    def __init__(self, code: int, message: str | None = None):
        self.code = code
        self.message = message or _ERROR_MESSAGES.get(code, "未知错误")
        super().__init__(self.message)


class NotLoginException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.NOT_LOGGED_IN, message)


class LoginFailedException(AppException):
    """账号不存在与密码错误必须返回完全相同的信息，避免账号枚举。"""

    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.LOGIN_FAILED, message)


class AlreadyRegisteredException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.ALREADY_REGISTERED, message)


class ForbiddenException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.FORBIDDEN, message)


class NotFoundException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.NOT_FOUND, message)


class ParamException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.PARAM_INVALID, message)


class StatusNotAllowedException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.STATUS_NOT_ALLOWED, message)


class MeetingRoomConflictException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.MEETING_ROOM_CONFLICT, message)


class EnterpriseRestrictedException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.ENTERPRISE_RESTRICTED, message)


class ThirdPartyAuthException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.THIRD_PARTY_AUTH_ERROR, message)


class FileUploadException(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(ErrorCode.FILE_UPLOAD_FAILED, message)


# ── Global Exception Handlers ─────────────────────────────────────────────────

def _trace() -> str:
    return uuid.uuid4().hex


def _json(code: int, message: str, http_status: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": None, "traceId": _trace()},
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _json(exc.code, exc.message)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = " -> ".join(str(x) for x in first_error.get("loc", []))
    msg = first_error.get("msg", "参数校验失败")
    return _json(ErrorCode.PARAM_INVALID, f"{loc}: {msg}" if loc else msg)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 401:
        return _json(ErrorCode.NOT_LOGGED_IN, "未登录", 200)
    if exc.status_code == 403:
        return _json(ErrorCode.FORBIDDEN, "无权限", 200)
    if exc.status_code == 404:
        return _json(ErrorCode.NOT_FOUND, "接口不存在", 200)
    return _json(ErrorCode.SYSTEM_ERROR, str(exc.detail), 200)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _json(ErrorCode.SYSTEM_ERROR, "系统异常，请稍后重试")
