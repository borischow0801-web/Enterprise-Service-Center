"""管理端正式登录（统一身份认证 BSPPLUS）端到端测试。

app/services/bsp_client.py::BspClient.login 全程 monkeypatch，不发起真实网络
请求——BspClient 自身的请求构造/响应解析已经在 tests/test_bsp_client.py 单测覆盖。
这里只测"登录编排 + 本地管理员匹配 + JWT 签发 + 既有 RBAC 执行链"这一段。
"""

import pytest

from app.constants.permission import DataScope
from app.models.system import AdminUserStatus, SysAdminUser, SysOperationLog
from app.services.bsp_client import BspAuthFailedException, BspClient, BspServiceException, BspUser
from tests.helpers import auth_headers, unique_admin_username, unique_bsp_user_id

LOGIN_URL = "/api/auth/admin/login"
ME_URL = "/api/admin/me"


def _fake_bsp_user(**overrides) -> BspUser:
    base = dict(
        id=unique_bsp_user_id(),
        username="probe",
        name="测试用户",
        mobile="13900001111",
        organ_code="org-1",
        organ_name="测试单位",
        region_code="370100",
        region_name="测试市",
    )
    base.update(overrides)
    return BspUser(**base)


def _patch_bsp_login(monkeypatch, result=None, exc=None):
    def fake_login(self, username, password):
        if exc is not None:
            raise exc
        return result

    monkeypatch.setattr(BspClient, "login", fake_login)


def _create_admin(db_session, **overrides) -> SysAdminUser:
    defaults = dict(
        bsp_user_id=None,
        username=unique_admin_username(),
        real_name="测试管理员",
        mobile=None,
        status=AdminUserStatus.ACTIVE,
        role_codes="CENTER_ADMIN",
        data_scope=DataScope.REGION,
        region_code="370100",
        region_name="测试市",
        department_id=None,
        department_name=None,
    )
    defaults.update(overrides)
    admin = SysAdminUser(**defaults)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


# ── 1: BSP 正确账号密码 + 已绑定 bsp_user_id → 登录成功，角色来自本地表 ────────────

def test_login_success_when_already_bound_by_bsp_user_id(client, db_session, monkeypatch):
    bsp_uid = unique_bsp_user_id()
    admin = _create_admin(
        db_session, bsp_user_id=bsp_uid, role_codes="CENTER_ADMIN,CENTER_STAFF", data_scope=DataScope.REGION,
    )
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=bsp_uid, username=admin.username))

    resp = client.post(LOGIN_URL, json={"username": admin.username, "password": "whatever-bsp-checks-this"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    token = body["data"]["accessToken"]
    assert token

    me = client.get(ME_URL, headers=auth_headers(token))
    me_body = me.json()
    assert me_body["code"] == 0
    assert me_body["data"]["id"] == admin.id
    assert sorted(me_body["data"]["roleCodes"]) == ["CENTER_ADMIN", "CENTER_STAFF"]
    assert me_body["data"]["dataScope"] == DataScope.REGION
    assert me_body["data"]["platformUserId"] == bsp_uid

    db_session.refresh(admin)
    assert admin.last_login_at is not None


# ── 2: BSP 错误账号密码 → 40102，且不暴露账号是否存在 ─────────────────────────────

def test_login_wrong_credentials_returns_login_failed(client, monkeypatch):
    _patch_bsp_login(monkeypatch, exc=BspAuthFailedException("账号或密码错误"))
    resp = client.post(LOGIN_URL, json={"username": "whoever", "password": "wrong"})
    body = resp.json()
    assert body["code"] == 40102
    assert body["message"] == "账号或密码错误"


# ── 3/4: BSP 网络异常（超时/5xx/连接失败等，均归一为 BspServiceException）──────────

def test_bsp_service_exception_returns_third_party_error_not_internal_details(client, monkeypatch):
    _patch_bsp_login(monkeypatch, exc=BspServiceException("统一身份认证服务暂时不可用"))
    resp = client.post(LOGIN_URL, json={"username": "whoever", "password": "whatever"})
    body = resp.json()
    assert body["code"] == 50002
    # 不泄露内网地址/底层异常类型等内部信息。
    assert "172.29.91.36" not in body["message"]
    assert "9099" not in body["message"]
    assert "Traceback" not in body["message"]


def test_bsp_unreachable_does_not_crash_backend(client, monkeypatch):
    """BSP 完全不可用时后端必须返回明确错误而不是 500/崩溃。"""
    _patch_bsp_login(monkeypatch, exc=BspServiceException("统一身份认证服务暂时不可用"))
    resp = client.post(LOGIN_URL, json={"username": "whoever", "password": "whatever"})
    assert resp.status_code == 200  # 统一响应包装，业务错误也是 HTTP 200 + 非0 code
    assert resp.json()["code"] == 50002


# ── 5: BSP 认证成功但本地未开通 → 拒绝，不自动创建 ────────────────────────────────

def test_bsp_success_but_no_local_admin_is_rejected(client, db_session, monkeypatch):
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(username=unique_admin_username()))
    resp = client.post(LOGIN_URL, json={"username": "nobody-provisioned", "password": "whatever"})
    body = resp.json()
    assert body["code"] == 40301
    assert "未开通" in body["message"]

    # 确认没有静默创建任何 sys_admin_user 记录。
    count = db_session.query(SysAdminUser).filter(SysAdminUser.username == "nobody-provisioned").count()
    assert count == 0


# ── 6: 本地管理员已绑定但 disabled → 拒绝 ─────────────────────────────────────────

def test_disabled_admin_rejected_even_with_correct_bsp_credentials(client, db_session, monkeypatch):
    bsp_uid = unique_bsp_user_id()
    admin = _create_admin(db_session, bsp_user_id=bsp_uid, status=AdminUserStatus.DISABLED)
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=bsp_uid, username=admin.username))

    resp = client.post(LOGIN_URL, json={"username": admin.username, "password": "whatever"})
    body = resp.json()
    assert body["code"] == 40301
    assert "禁用" in body["message"]


# ── 7/8: 首次 username 安全绑定 ──────────────────────────────────────────────────

def test_first_time_username_bind_succeeds_and_is_logged(client, db_session, monkeypatch):
    admin = _create_admin(db_session, bsp_user_id=None, role_codes="PLATFORM_ADMIN", data_scope=DataScope.ALL)
    bsp_uid = unique_bsp_user_id()
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=bsp_uid, username=admin.username))

    resp = client.post(LOGIN_URL, json={"username": admin.username, "password": "whatever"})
    body = resp.json()
    assert body["code"] == 0

    db_session.refresh(admin)
    assert admin.bsp_user_id == bsp_uid

    log = db_session.query(SysOperationLog).filter(
        SysOperationLog.business_type == "ADMIN_USER",
        SysOperationLog.operation_type == "BSP_BIND",
        SysOperationLog.business_id == admin.id,
    ).first()
    assert log is not None
    assert bsp_uid in log.operation_content


def test_bind_does_not_hijack_admin_already_bound_to_different_bsp_user(client, db_session, monkeypatch):
    """规则 4/8：bsp_user_id 已非空时，不允许被另一个 BSP 账号顶替绑定。"""
    original_bsp_uid = unique_bsp_user_id()
    admin = _create_admin(db_session, bsp_user_id=original_bsp_uid)
    other_bsp_uid = unique_bsp_user_id()
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=other_bsp_uid, username=admin.username))

    resp = client.post(LOGIN_URL, json={"username": admin.username, "password": "whatever"})
    assert resp.json()["code"] == 40301  # 未开通（同一账号名，但 bsp_user_id 已绑定给别人）

    db_session.refresh(admin)
    assert admin.bsp_user_id == original_bsp_uid  # 没有被静默覆盖


def test_one_bsp_user_cannot_end_up_bound_to_two_local_admins(client, db_session, monkeypatch):
    bsp_uid = unique_bsp_user_id()
    _create_admin(db_session, bsp_user_id=bsp_uid, username=unique_admin_username())
    admin2 = _create_admin(db_session, bsp_user_id=None, username=unique_admin_username())

    # admin2 尝试用同一个 bsp_uid 登录（模拟 BSP 侧返回同一个 user.id）——
    # get_by_bsp_user_id 应命中第一个已绑定的账号，而不是让 admin2 也绑上同一个 id。
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=bsp_uid, username=admin2.username))
    resp = client.post(LOGIN_URL, json={"username": admin2.username, "password": "whatever"})
    body = resp.json()
    assert body["code"] == 0  # 命中的是第一个 admin（按 bsp_user_id 匹配优先）

    db_session.refresh(admin2)
    assert admin2.bsp_user_id is None  # admin2 没有被绑定


# ── 9/10: 角色来自本地库，登录请求无法伪造 roleCodes/dataScope ───────────────────

def test_login_request_cannot_inject_role_codes_or_data_scope(client, db_session, monkeypatch):
    admin = _create_admin(db_session, role_codes="CENTER_STAFF", data_scope=DataScope.SELF)
    bsp_uid = admin.bsp_user_id
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=bsp_uid, username=admin.username))

    resp = client.post(LOGIN_URL, json={
        "username": admin.username,
        "password": "whatever",
        "roleCodes": ["PLATFORM_ADMIN"],   # AdminLoginRequest 里根本没有这个字段，应被忽略
        "dataScope": "ALL",
    })
    body = resp.json()
    assert body["code"] == 0
    token = body["data"]["accessToken"]

    me = client.get(ME_URL, headers=auth_headers(token))
    me_data = me.json()["data"]
    assert me_data["roleCodes"] == ["CENTER_STAFF"]  # 仍然是本地库里的角色，没被请求体覆盖
    assert me_data["dataScope"] == DataScope.SELF


# ── 11/12/13: /api/admin/me、require_permissions、data_scope 对 BSP 登录同样生效 ──

def test_require_permissions_enforced_for_bsp_issued_token(client, db_session, monkeypatch):
    admin = _create_admin(db_session, role_codes="CENTER_STAFF", data_scope=DataScope.REGION)
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=admin.bsp_user_id, username=admin.username))
    token = client.post(LOGIN_URL, json={"username": admin.username, "password": "x"}).json()["data"]["accessToken"]

    # CENTER_STAFF 没有 DICT_MANAGE 权限，新增服务中心应被拒绝——证明既有
    # require_permissions 逻辑对 BSP 签发的 token 同样生效，未被绕过。
    resp = client.post(
        "/api/admin/service-centers",
        headers=auth_headers(token),
        json={"centerName": "不该被创建的中心", "regionCode": "370100", "regionName": "测试市"},
    )
    assert resp.json()["code"] == 40301


def test_data_scope_region_enforced_for_bsp_issued_token(client, db_session, monkeypatch):
    admin = _create_admin(
        db_session, role_codes="PLATFORM_ADMIN", data_scope=DataScope.REGION, region_code="370100",
    )
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=admin.bsp_user_id, username=admin.username))
    token = client.post(LOGIN_URL, json={"username": admin.username, "password": "x"}).json()["data"]["accessToken"]

    resp = client.get("/api/admin/service-centers", params={"regionCode": "999999"}, headers=auth_headers(token))
    # REGION 数据权限下只能看自己 region_code 的数据；查询别的 regionCode 应返回空列表
    # （既有 app/api/admin/router.py::list_service_centers 的过滤逻辑，未被本次改动影响）。
    assert resp.json()["data"] == []


# ── ADMIN_USER_MANAGE 权限收紧：CENTER_ADMIN 不能管理管理员账号 ───────────────────

def test_center_admin_cannot_manage_admin_users(client, db_session, monkeypatch):
    admin = _create_admin(db_session, role_codes="CENTER_ADMIN", data_scope=DataScope.REGION)
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=admin.bsp_user_id, username=admin.username))
    token = client.post(LOGIN_URL, json={"username": admin.username, "password": "x"}).json()["data"]["accessToken"]

    resp = client.get("/api/admin/admin-users/page", headers=auth_headers(token))
    assert resp.json()["code"] == 40301


def test_platform_admin_can_manage_admin_users(client, db_session, monkeypatch):
    admin = _create_admin(db_session, role_codes="PLATFORM_ADMIN", data_scope=DataScope.ALL)
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=admin.bsp_user_id, username=admin.username))
    token = client.post(LOGIN_URL, json={"username": admin.username, "password": "x"}).json()["data"]["accessToken"]

    new_username = unique_admin_username()
    create_resp = client.post(
        "/api/admin/admin-users",
        headers=auth_headers(token),
        json={
            "username": new_username,
            "realName": "新建管理员",
            "roleCodes": ["CENTER_STAFF"],
            "dataScope": "SELF",
            "regionCode": "370100",
            "regionName": "测试市",
        },
    )
    body = create_resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == new_username
    assert body["data"]["status"] == "ACTIVE"

    list_resp = client.get(
        "/api/admin/admin-users/page", params={"username": new_username}, headers=auth_headers(token)
    )
    assert list_resp.json()["data"]["total"] == 1

    # 禁用
    admin_id = body["data"]["id"]
    disable_resp = client.patch(
        f"/api/admin/admin-users/{admin_id}/status", headers=auth_headers(token), json={"status": "DISABLED"}
    )
    assert disable_resp.json()["data"]["status"] == "DISABLED"


# ── 14/15: mock-login 环境隔离（回归，确保本次改动未影响既有网关）─────────────────

def test_admin_mock_login_still_works_in_development(client):
    resp = client.post("/api/auth/admin/mock-login", json={
        "platformUserId": "mock-check-001", "username": "mockuser", "realName": "Mock用户",
        "departmentId": "d1", "departmentName": "d1", "regionCode": "370100", "regionName": "测试市",
        "roleCodes": ["CENTER_STAFF"], "dataScope": "SELF",
    })
    assert resp.json()["code"] == 0


def test_admin_mock_login_still_blocked_in_production(client, as_production_env):
    resp = client.post("/api/auth/admin/mock-login", json={
        "platformUserId": "mock-check-002", "username": "mockuser", "realName": "Mock用户",
        "departmentId": "d1", "departmentName": "d1", "regionCode": "370100", "regionName": "测试市",
        "roleCodes": ["CENTER_STAFF"], "dataScope": "SELF",
    })
    assert resp.json()["code"] == 40401

    # 生产环境下正式登录端点必须仍然可达（只是本例中 BSP 未配置会报 50002，
    # 但绝不能是 mock-login 那种"接口不存在"的 40401——两者是完全独立的开关）。
    real_resp = client.post("/api/auth/admin/login", json={"username": "x", "password": "y"})
    assert real_resp.json()["code"] != 40401


# ── 17: 密码不出现在响应/异常信息里（黑盒层面的抽查）──────────────────────────────

def test_password_never_echoed_back_in_any_response(client, monkeypatch):
    secret = "Sup3r-Secret-Pwd-Value"
    _patch_bsp_login(monkeypatch, exc=BspAuthFailedException("账号或密码错误"))
    resp = client.post(LOGIN_URL, json={"username": "whoever", "password": secret})
    assert secret not in resp.text


# ── 18: BSP token/refreshToken 不会出现在返回给前端的数据里 ──────────────────────

def test_bsp_token_and_refresh_token_never_reach_frontend_response(client, db_session, monkeypatch):
    admin = _create_admin(db_session)
    _patch_bsp_login(monkeypatch, result=_fake_bsp_user(id=admin.bsp_user_id, username=admin.username))
    resp = client.post(LOGIN_URL, json={"username": admin.username, "password": "x"})
    body = resp.json()
    assert body["code"] == 0
    data_keys = set(body["data"].keys())
    assert data_keys == {"accessToken", "tokenType", "expiresIn"}
    assert "refreshToken" not in body["data"]
    assert "bspToken" not in body["data"]
