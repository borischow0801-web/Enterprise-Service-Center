"""
Unified response format:
  {
    "code": 0,
    "message": "success",
    "data": {},
    "traceId": "<uuid>"
  }

Paginated data field:
  {
    "records": [],
    "total": 0,
    "pageNo": 1,
    "pageSize": 10
  }
"""

import uuid
from typing import Any

from fastapi.responses import JSONResponse


def _trace_id() -> str:
    return uuid.uuid4().hex


def success(data: Any = None, message: str = "success", trace_id: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": 0,
            "message": message,
            "data": data,
            "traceId": trace_id or _trace_id(),
        },
    )


def paginated(
    records: list[Any],
    total: int,
    page_no: int = 1,
    page_size: int = 10,
    message: str = "success",
    trace_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": 0,
            "message": message,
            "data": {
                "records": records,
                "total": total,
                "pageNo": page_no,
                "pageSize": page_size,
            },
            "traceId": trace_id or _trace_id(),
        },
    )


def error(
    code: int,
    message: str,
    http_status: int = 200,
    trace_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": message,
            "data": None,
            "traceId": trace_id or _trace_id(),
        },
    )
