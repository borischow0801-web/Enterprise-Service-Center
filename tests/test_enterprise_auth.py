"""
Tests for enterprise LOCAL self-registration + password login
(app/services/enterprise_auth_service.py, app/api/auth/router.py).
"""

from app.models.enterprise import Enterprise, EnterpriseIdentity, EnterpriseIdentityType
from tests.helpers import register_and_login, unique_credit_code, unique_mobile

REGISTER_URL = "/api/auth/enterprise/register"
LOGIN_URL = "/api/auth/enterprise/login"
MOCK_LOGIN_URL = "/api/auth/enterprise/mock-login"


def _payload(**overrides) -> dict:
    credit_code = overrides.pop("creditCode", unique_credit_code())
    base = {
        "enterpriseName": "测试自主注册企业",
        "creditCode": credit_code,
        "contactName": "李四",
        "contactMobile": unique_mobile(),
        "password": "Passw0rd1",
        "confirmPassword": "Passw0rd1",
    }
    base.update(overrides)
    return base


# ── 1/2/3/4: 注册成功、Enterprise/LOCAL Identity 正确创建、密码非明文 ──────────────

def test_register_new_enterprise_success(client, db_session):
    payload = _payload()
    resp = client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["accessToken"]

    enterprise = db_session.query(Enterprise).filter(
        Enterprise.credit_code == payload["creditCode"]
    ).first()
    assert enterprise is not None
    assert enterprise.enterprise_name == payload["enterpriseName"]
    assert enterprise.auth_source == "LOCAL"
    # 法人字段本地注册阶段不采集，必须保持为空，不能塞入联系人数据冒充法人信息。
    assert enterprise.legal_person_name is None
    assert enterprise.legal_person_id_no is None

    identity = db_session.query(EnterpriseIdentity).filter(
        EnterpriseIdentity.enterprise_id == enterprise.id,
        EnterpriseIdentity.identity_type == EnterpriseIdentityType.LOCAL,
    ).first()
    assert identity is not None
    assert identity.identifier == payload["creditCode"]
    assert identity.contact_name == payload["contactName"]

    # 密码必须已被 hash，且不是明文、不是简单可逆编码。
    assert identity.credential_hash is not None
    assert identity.credential_hash != payload["password"]
    assert identity.credential_hash.startswith("$2b$")


# ── 5: 已有 Enterprise（无 LOCAL 身份）注册时应绑定而非重复创建 ──────────────────

def test_register_binds_existing_enterprise_without_duplicating(client, db_session):
    credit_code = unique_credit_code()
    existing = Enterprise(
        enterprise_name="老企业(通过mock-login创建)",
        credit_code=credit_code,
        auth_source="MOCK",
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)

    resp = client.post(REGISTER_URL, json=_payload(creditCode=credit_code, enterpriseName="老企业(注册时填写的名称)"))
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

    all_enterprises = db_session.query(Enterprise).filter(
        Enterprise.credit_code == credit_code
    ).all()
    assert len(all_enterprises) == 1  # 没有重复创建企业
    assert all_enterprises[0].id == existing.id
    assert all_enterprises[0].enterprise_name == "老企业(通过mock-login创建)"  # 未被注册请求覆盖
    assert all_enterprises[0].auth_source == "MOCK"  # 原始来源不变

    identity = db_session.query(EnterpriseIdentity).filter(
        EnterpriseIdentity.enterprise_id == existing.id
    ).first()
    assert identity is not None
    assert identity.identity_type == EnterpriseIdentityType.LOCAL


# ── 6: 已注册企业重复注册应失败 ──────────────────────────────────────────────

def test_register_duplicate_rejected(client):
    payload = _payload()
    first = client.post(REGISTER_URL, json=payload)
    assert first.json()["code"] == 0

    second = client.post(REGISTER_URL, json=payload)
    body = second.json()
    assert body["code"] == 40904
    assert "已注册" in body["message"]


# ── 7/8/9: 登录成功/密码错误/账号不存在，且后两者返回信息必须一致（防枚举） ─────────

def test_login_success(client):
    acc = register_and_login(client)
    resp = client.post(LOGIN_URL, json={"creditCode": acc["creditCode"], "password": acc["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["accessToken"]


def test_login_wrong_password_fails(client):
    acc = register_and_login(client)
    resp = client.post(LOGIN_URL, json={"creditCode": acc["creditCode"], "password": "WrongPassword1"})
    body = resp.json()
    assert body["code"] == 40102
    assert body["message"] == "账号或密码错误"


def test_login_nonexistent_account_fails_with_identical_message(client):
    resp = client.post(LOGIN_URL, json={
        "creditCode": unique_credit_code(),
        "password": "WhoKnows123",
    })
    body = resp.json()
    assert body["code"] == 40102
    assert body["message"] == "账号或密码错误"  # 与密码错误返回完全一致，不泄露账号是否存在


# ── 10/11: JWT 能通过 get_current_enterprise，并能调用现有企业端业务接口 ─────────

def test_login_token_can_access_existing_business_endpoint(client):
    acc = register_and_login(client)
    login_resp = client.post(LOGIN_URL, json={"creditCode": acc["creditCode"], "password": acc["password"]})
    token = login_resp.json()["data"]["accessToken"]

    me_resp = client.get("/api/enterprise/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["code"] == 0
    assert me_body["data"]["creditCode"] == acc["creditCode"]

    # 未改动过的既有企业端业务接口（诉求列表）——证明三大业务模块无需任何改动
    # 即可识别新登录方式签发的 token。
    appeals_resp = client.get("/api/enterprise/appeals", headers={"Authorization": f"Bearer {token}"})
    assert appeals_resp.status_code == 200
    assert appeals_resp.json()["code"] == 0

    # 未带 token 应被 get_current_enterprise 拒绝
    no_auth_resp = client.get("/api/enterprise/me")
    assert no_auth_resp.json()["code"] == 40101


# ── 12/13: mock-login 环境隔离 ──────────────────────────────────────────────

def test_mock_login_allowed_in_development(client):
    resp = client.post(MOCK_LOGIN_URL, json={
        "enterpriseName": "测试企业",
        "creditCode": unique_credit_code(),
        "legalPersonName": "张三",
        "legalPersonIdNo": "370000000000000000",
        "legalPersonMobile": "13800000000",
    })
    assert resp.json()["code"] == 0


def test_mock_login_blocked_in_production(client, as_production_env):
    resp = client.post(MOCK_LOGIN_URL, json={
        "enterpriseName": "测试企业",
        "creditCode": unique_credit_code(),
        "legalPersonName": "张三",
        "legalPersonIdNo": "370000000000000000",
        "legalPersonMobile": "13800000000",
    })
    body = resp.json()
    assert body["code"] == 40401
    # 真正的登录方式在生产环境必须继续可用，不受 mock-login 网关影响。
    login_resp = client.post(REGISTER_URL, json=_payload())
    assert login_resp.json()["code"] == 0


def test_admin_mock_login_blocked_in_production(client, as_production_env):
    resp = client.post("/api/auth/admin/mock-login", json={
        "platformUserId": "u_prod_check", "username": "x", "realName": "x",
        "departmentId": "d", "departmentName": "d", "regionCode": "r", "regionName": "r",
        "roleCodes": ["CENTER_ADMIN"], "dataScope": "ALL",
    })
    assert resp.json()["code"] == 40401


# ── 参数校验：格式与强度 ──────────────────────────────────────────────────────

def test_register_rejects_weak_password(client):
    resp = client.post(REGISTER_URL, json=_payload(password="12345678", confirmPassword="12345678"))
    assert resp.json()["code"] == 40001


def test_register_rejects_invalid_credit_code(client):
    resp = client.post(REGISTER_URL, json=_payload(creditCode="not-a-valid-code"))
    assert resp.json()["code"] == 40001


def test_register_rejects_invalid_mobile(client):
    resp = client.post(REGISTER_URL, json=_payload(contactMobile="12345"))
    assert resp.json()["code"] == 40001


def test_register_rejects_mismatched_passwords(client):
    resp = client.post(REGISTER_URL, json=_payload(confirmPassword="Different1"))
    assert resp.json()["code"] == 40001


# ── Migration revision 链路完整性（轻量 sanity check；真正的 upgrade 已在
#    真实 MySQL 开发库上验证，见 docs/ENTERPRISE_AUTH_IMPLEMENTATION.md） ─────

def test_migration_chain_links_to_head():
    import importlib

    mod = importlib.import_module("migrations.versions.010_enterprise_identity")
    assert mod.revision == "010_enterprise_identity"
    assert mod.down_revision == "009_booking_enterprise_type"
