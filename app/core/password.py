"""
Password hashing for local (LOCAL) enterprise accounts.

`passlib[bcrypt]==1.7.4` (declared in requirements.txt) was verified against the
currently installed `bcrypt` package and found broken: passlib's bcrypt backend
probes `bcrypt.__about__.__version__`, which was removed in bcrypt>=4.1, causing
`AttributeError`/`ValueError` on every hash/verify call. passlib itself has been
unmaintained since 2020 with known incompatibilities against modern bcrypt.

Rather than pin an old bcrypt to keep an unmaintained wrapper alive, this module
calls the `bcrypt` library directly — it is itself the mature, audited primitive
passlib was only wrapping, so this is not "rolling our own crypto".
"""

import re

import bcrypt

from app.core.exceptions import ParamException

_BCRYPT_ROUNDS = 12
_MAX_PASSWORD_BYTES = 72  # bcrypt hard limit


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password. Never log or persist the plaintext anywhere."""
    encoded = plain_password.encode("utf-8")
    if len(encoded) > _MAX_PASSWORD_BYTES:
        raise ParamException(f"密码长度不能超过 {_MAX_PASSWORD_BYTES} 字节")
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time verify. Returns False on any malformed hash rather than raising,
    so callers can treat it the same as "wrong password"."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 64
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def assert_password_strength(password: str) -> str:
    """Baseline strength check: 8-64 chars, at least one letter and one digit.
    Raises ValueError (for use inside pydantic validators) on failure."""
    if not isinstance(password, str) or len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"密码长度不能少于 {_PASSWORD_MIN_LENGTH} 位")
    if len(password) > _PASSWORD_MAX_LENGTH:
        raise ValueError(f"密码长度不能超过 {_PASSWORD_MAX_LENGTH} 位")
    if len(password.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise ValueError("密码包含过多多字节字符，请缩短或改用英文数字")
    if not _HAS_LETTER.search(password) or not _HAS_DIGIT.search(password):
        raise ValueError("密码必须同时包含字母和数字")
    return password
