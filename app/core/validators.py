"""Shared format validators for request schemas.

These raise plain ValueError so they can be dropped directly into pydantic
`field_validator`s — FastAPI turns that into a RequestValidationError, which the
app's existing global handler (app.core.exceptions.validation_exception_handler)
already converts into the unified {code: 40001, message: "..."} response shape.
"""

import re

_CREDIT_CODE_RE = re.compile(r"^[0-9A-Z]{18}$")
_MOBILE_RE = re.compile(r"^1[3-9]\d{9}$")


def validate_credit_code(value: str) -> str:
    value = (value or "").strip().upper()
    if not _CREDIT_CODE_RE.match(value):
        raise ValueError("统一社会信用代码格式不正确，应为18位数字/大写字母")
    return value


def validate_mobile(value: str) -> str:
    value = (value or "").strip()
    if not _MOBILE_RE.match(value):
        raise ValueError("手机号格式不正确")
    return value
