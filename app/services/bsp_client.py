"""BSPPLUS（浪潮政务服务基础服务）统一身份认证 HTTP 客户端。

只实现《011浪潮政务服务基础服务bspplus对接规范v1.2.docx》3.3.1 "通用用户登录接口"
（POST /user/login）——这是本次管理端改造唯一确认采用的登录方式。不实现文档中
其他登录/单点登录接口。

设计原则（对应改造需求第七节）：
  - 不直接被 /api/auth/admin/login 路由调用，中间隔着 AdminAuthService，
    本模块只负责"和 BSP 说话"，不知道本系统的用户/角色概念。
  - 必须设置 connect/read timeout，不允许无限等待。
  - 不记录密码、不记录 BSP 返回的 token/refreshToken 明文到日志。
  - 对外只抛出本模块定义的两类异常，调用方据此转换成用户可见的错误提示，
    不把 BSP 原始响应体/异常堆栈/内部地址透出。

⚠️ password 加密方式标记："待真实 BSP 联调确认"：
    文档 3.3.1 对 password 的说明只写"密码（加密）"，没有指明具体算法；但文档
    在 3.3.1 与 3.3.6（kms 登录，明确写"密码（MD5加密）"）两处给出的请求示例
    密码值都是同一个 32 位十六进制串（"5fa4fe49a0f447458fce93195af6c81c"），
    且同环境下另一个已在生产真实对接 BSPPLUS 的项目（/app/OMS/backend/apps/
    accounts/bspplus_service.py）实测确认为 MD5(password) 十六进制小写摘要。
    这是两个独立证据的推断，不是凭空假设，但文档本身没有逐字确认，因此仍标记
    为待真实环境联调验证；一旦联调发现不一致，只需改 _encrypt_password 一处。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from hashlib import md5
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class BspAuthFailedException(Exception):
    """BSP 明确判定账号/密码不合法（业务级失败，不是网络/协议异常）。"""


class BspServiceException(Exception):
    """BSP 不可达、超时、返回格式异常等——不能判断账号密码是否正确的所有情况。"""


@dataclass
class BspUser:
    """BSP /user/login 返回的 data.user，仅保留本系统会用到的字段。"""

    id: str
    username: str
    name: str
    mobile: str | None
    organ_code: str | None
    organ_name: str | None
    region_code: str | None
    region_name: str | None


def _encrypt_password(raw_password: str) -> str:
    return md5(raw_password.encode("utf-8")).hexdigest()


def _mask(value: str | None, keep: int = 2) -> str:
    """仅用于内部日志：保留前 keep 位，其余打码，从不记录明文密码/token。"""
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


class BspClient:
    """薄封装：只负责一次 BSP /user/login 调用，不持有任何会话状态。

    `transport` 仅供测试注入 `httpx.MockTransport`，模拟 BSP 的各种响应/网络异常，
    不在生产路径上使用（生产环境不传，走 httpx 默认的真实网络传输）。
    """

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._api_root = (settings.bspplus_api_root or "").rstrip("/")
        self._app_code = settings.bspplus_app_code
        self._transport = transport
        self._timeout = httpx.Timeout(
            connect=settings.bspplus_connect_timeout_seconds,
            read=settings.bspplus_read_timeout_seconds,
            write=settings.bspplus_read_timeout_seconds,
            pool=settings.bspplus_connect_timeout_seconds,
        )

    def login(self, username: str, password: str) -> BspUser:
        if not self._api_root or not self._app_code:
            # 未配置 BSPPLUS 对接信息（例如尚未拿到生产地址前的开发阶段）。
            logger.error("BSPPLUS 未配置（BSPPLUS_API_ROOT/BSPPLUS_APP_CODE 缺失），无法完成统一身份认证")
            raise BspServiceException("统一身份认证服务未配置")

        url = f"{self._api_root}/user/login"
        payload = {
            "username": username,
            "password": _encrypt_password(password),
            "appCode": self._app_code,
        }

        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
        except httpx.TimeoutException:
            logger.error("BSPPLUS 登录请求超时 username=%s", _mask(username))
            raise BspServiceException("统一身份认证服务响应超时")
        except httpx.RequestError as exc:
            logger.error("BSPPLUS 登录请求失败 username=%s error=%s", _mask(username), exc.__class__.__name__)
            raise BspServiceException("统一身份认证服务暂时不可用")

        if resp.status_code >= 500:
            logger.error("BSPPLUS 返回服务端错误 status=%s username=%s", resp.status_code, _mask(username))
            raise BspServiceException("统一身份认证服务暂时不可用")
        if resp.status_code >= 400:
            logger.error("BSPPLUS 返回客户端错误 status=%s username=%s", resp.status_code, _mask(username))
            raise BspServiceException("统一身份认证服务请求异常")

        try:
            body = resp.json()
        except ValueError:
            logger.error("BSPPLUS 响应无法解析为 JSON username=%s", _mask(username))
            raise BspServiceException("统一身份认证服务响应格式异常")

        if not isinstance(body, dict):
            logger.error("BSPPLUS 响应不是 JSON 对象 username=%s", _mask(username))
            raise BspServiceException("统一身份认证服务响应格式异常")

        # 文档 3.3.1：成功时 code=1 且 data.flag=true。code!=1 是 BSP 明确的业务级判定
        # （账号/密码错误等），与"code=1 但 data 结构缺失"（协议异常，不能当成"密码错误"
        # 处理）必须分开：后者可能是 BSP 版本差异或网关异常，不应该误导用户去改密码。
        if body.get("code") != 1:
            msg = body.get("msg") or "账号或密码错误"
            logger.info("BSPPLUS 认证未通过 username=%s msg=%s", _mask(username), msg)
            raise BspAuthFailedException(msg)

        data = body.get("data")
        if not isinstance(data, dict):
            logger.error("BSPPLUS 返回 code=1 但 data 字段缺失/格式异常 username=%s", _mask(username))
            raise BspServiceException("统一身份认证服务响应异常")

        if data.get("flag") is not True:
            msg = body.get("msg") or "账号或密码错误"
            logger.info("BSPPLUS 认证未通过 username=%s msg=%s", _mask(username), msg)
            raise BspAuthFailedException(msg)

        user = data.get("user")
        if not isinstance(user, dict) or not user.get("id"):
            # flag=true 但缺少 user.id——协议异常，不能用于匹配本地管理员。
            logger.error("BSPPLUS 登录成功但响应缺少 user.id username=%s", _mask(username))
            raise BspServiceException("统一身份认证服务响应异常")

        # data.token / data.refreshToken 在此有意不读取、不透传、不落盘——
        # 本系统不使用 BSP token 维持业务会话（见改造背景第七节）。
        return BspUser(
            id=str(user["id"]),
            username=user.get("username") or username,
            name=user.get("name") or "",
            mobile=user.get("phone") or None,
            organ_code=user.get("organCode") or None,
            organ_name=user.get("organName") or None,
            region_code=user.get("regionCode") or None,
            region_name=user.get("regionName") or None,
        )
