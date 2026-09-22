"""BspClient 单测：请求构造、密码处理、响应解析、异常转换。

全部使用 httpx.MockTransport 模拟 BSP，不发起真实网络请求——真实 BSP
(172.29.91.36:9099，政务内网) 在本开发环境不可达，且 CI/pytest 不应长期
依赖真实 BSP 才能跑通（见改造需求第五节）。真实联调用 scripts/bspplus_login_check.py。

虚构测试数据：账号/密码/BSP user.id 均为本测试编造的占位值，不是文档里的
真实示例（避免把文档中的示例 token/账号 当成项目测试数据）。
"""

import hashlib

import httpx
import pytest

from app.core.config import settings
from app.services.bsp_client import BspAuthFailedException, BspClient, BspServiceException


@pytest.fixture(autouse=True)
def _bsp_configured(monkeypatch):
    """给 BspClient 一个非空的 api_root/app_code，让"未配置"分支不会提前拦截。"""
    monkeypatch.setattr(settings, "bspplus_api_root", "http://bsp.invalid:9099")
    monkeypatch.setattr(settings, "bspplus_app_code", "esc-admin-test")


def _client_with(handler) -> BspClient:
    return BspClient(transport=httpx.MockTransport(handler))


def _success_body(user_overrides: dict | None = None) -> dict:
    user = {
        "id": "bsp-uid-0001",
        "username": "zhangsan_test",
        "name": "张三(测试)",
        "phone": "13900000001",
        "organCode": "org-001",
        "organName": "测试单位",
        "regionCode": "370100",
        "regionName": "测试市",
    }
    if user_overrides:
        user.update(user_overrides)
    return {
        "code": 1,
        "msg": "ok",
        "data": {
            "flag": True,
            "user": user,
            "token": "fake-bsp-token-not-a-real-jwt",
            "refreshToken": "fake-bsp-refresh-token",
        },
        "status": 200,
    }


# ── 请求构造：URL / method / Content-Type / body / password 处理 ────────────────

def test_login_request_is_constructed_per_doc():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers.get("content-type")
        captured["body"] = __import__("json").loads(request.content)
        return httpx.Response(200, json=_success_body())

    client = _client_with(handler)
    client.login("zhangsan_test", "MyP@ssw0rd")

    assert captured["method"] == "POST"
    assert captured["url"] == "http://bsp.invalid:9099/user/login"
    assert captured["content_type"] == "application/json"
    assert captured["body"]["username"] == "zhangsan_test"
    assert captured["body"]["appCode"] == "esc-admin-test"
    # password 必须已加密，不是明文；标记为"按文档示例格式(32位hex)推断为 MD5，
    # 待真实 BSP 联调确认"，见 bsp_client.py 顶部说明。
    assert captured["body"]["password"] != "MyP@ssw0rd"
    assert captured["body"]["password"] == hashlib.md5(b"MyP@ssw0rd").hexdigest()
    assert len(captured["body"]["password"]) == 32


def test_login_success_parses_user_fields():
    client = _client_with(lambda req: httpx.Response(200, json=_success_body()))
    user = client.login("zhangsan_test", "MyP@ssw0rd")

    assert user.id == "bsp-uid-0001"
    assert user.username == "zhangsan_test"
    assert user.name == "张三(测试)"
    assert user.mobile == "13900000001"
    assert user.organ_code == "org-001"
    assert user.region_code == "370100"
    assert user.region_name == "测试市"


# ── BSP 明确判定失败（业务级）──────────────────────────────────────────────────

def test_wrong_username_or_password_raises_auth_failed():
    body = {"code": 0, "msg": "账号或密码错误", "data": {"flag": False}, "status": 200}
    client = _client_with(lambda req: httpx.Response(200, json=body))
    with pytest.raises(BspAuthFailedException):
        client.login("zhangsan_test", "wrong-password")


def test_flag_false_raises_auth_failed():
    body = {"code": 1, "msg": "ok", "data": {"flag": False}, "status": 200}
    client = _client_with(lambda req: httpx.Response(200, json=body))
    with pytest.raises(BspAuthFailedException):
        client.login("zhangsan_test", "whatever")


# ── 网络/协议异常：一律 BspServiceException，不能判断账号密码是否正确 ─────────────

def test_http_4xx_raises_service_exception():
    client = _client_with(lambda req: httpx.Response(404, text="not found"))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_http_5xx_raises_service_exception():
    client = _client_with(lambda req: httpx.Response(500, text="internal error"))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_timeout_raises_service_exception():
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("timed out", request=request)

    client = _client_with(handler)
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_connection_error_raises_service_exception():
    def handler(request: httpx.Request):
        raise httpx.ConnectError("connection refused", request=request)

    client = _client_with(handler)
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_malformed_json_raises_service_exception():
    client = _client_with(lambda req: httpx.Response(200, text="<html>not json</html>"))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_empty_data_raises_service_exception():
    body = {"code": 1, "msg": "ok", "data": None, "status": 200}
    client = _client_with(lambda req: httpx.Response(200, json=body))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_success_but_missing_user_id_raises_service_exception():
    body = _success_body()
    del body["data"]["user"]["id"]
    client = _client_with(lambda req: httpx.Response(200, json=body))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_success_flag_but_user_not_object_raises_service_exception():
    body = {"code": 1, "msg": "ok", "data": {"flag": True, "user": "not-a-dict"}, "status": 200}
    client = _client_with(lambda req: httpx.Response(200, json=body))
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


def test_unconfigured_api_root_raises_service_exception_without_network(monkeypatch):
    monkeypatch.setattr(settings, "bspplus_api_root", "")
    client = BspClient()
    with pytest.raises(BspServiceException):
        client.login("zhangsan_test", "whatever")


# ── 敏感信息不落日志（抽查：异常信息本身不包含明文密码）───────────────────────────

def test_exception_message_never_contains_plain_password():
    body = {"code": 0, "msg": "账号或密码错误", "data": {"flag": False}, "status": 200}
    client = _client_with(lambda req: httpx.Response(200, json=body))
    secret = "S3cr3t-Plain-Password"
    try:
        client.login("zhangsan_test", secret)
    except BspAuthFailedException as exc:
        assert secret not in str(exc)
