"""Shared helpers for the regression suite.

Tests run against the real (shared) dev MySQL database (see conftest.py) — every
identifier a test creates must be unique enough to never collide with real,
pre-existing data (including data left behind by manual/ad-hoc testing during
development). Never reuse fixed literal credit codes / platform user ids across
tests for this reason.
"""

import secrets


def unique_credit_code() -> str:
    """18 chars, matches the backend's [0-9A-Z]{18} validator."""
    return "91" + secrets.token_hex(8).upper()


def unique_mobile() -> str:
    return "138" + str(secrets.randbelow(10**8)).zfill(8)


def unique_platform_user_id(prefix: str = "u") -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


def unique_bsp_user_id() -> str:
    return f"bsp_{secrets.token_hex(10)}"


def unique_admin_username() -> str:
    return f"admin_{secrets.token_hex(6)}"


def register_and_login(client, *, credit_code: str | None = None, password: str = "Passw0rd1", **overrides) -> dict:
    """Registers a fresh enterprise and returns {token, creditCode, password}."""
    credit_code = credit_code or unique_credit_code()
    payload = {
        "enterpriseName": overrides.pop("enterpriseName", f"测试企业{credit_code[-6:]}"),
        "creditCode": credit_code,
        "contactName": overrides.pop("contactName", "测试联系人"),
        "contactMobile": overrides.pop("contactMobile", unique_mobile()),
        "password": password,
        "confirmPassword": password,
        **overrides,
    }
    resp = client.post("/api/auth/enterprise/register", json=payload)
    assert resp.status_code == 200 and resp.json()["code"] == 0, resp.text
    token = resp.json()["data"]["accessToken"]
    return {"token": token, "creditCode": credit_code, "password": password}


def admin_login(
    client,
    *,
    region_code: str,
    role_codes: list[str],
    data_scope: str,
    department_id: str | None = None,
    **overrides,
) -> str:
    """Mock-logs-in an admin (dev-only endpoint) and returns the access token."""
    payload = {
        "platformUserId": unique_platform_user_id(),
        "username": overrides.pop("username", "test_admin"),
        "realName": overrides.pop("realName", "测试管理员"),
        "departmentId": department_id or unique_platform_user_id("dept"),
        "departmentName": overrides.pop("departmentName", "测试部门"),
        "regionCode": region_code,
        "regionName": overrides.pop("regionName", "测试区域"),
        "roleCodes": role_codes,
        "dataScope": data_scope,
        **overrides,
    }
    resp = client.post("/api/auth/admin/mock-login", json=payload)
    assert resp.status_code == 200 and resp.json()["code"] == 0, resp.text
    return resp.json()["data"]["accessToken"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def upload_pdf(client, token: str, filename: str = "test.pdf") -> int:
    resp = client.post(
        "/api/common/attachments/upload",
        headers=auth_headers(token),
        files={"file": (filename, b"%PDF-1.4 test content", "application/pdf")},
    )
    assert resp.json()["code"] == 0, resp.text
    return resp.json()["data"]["id"]


def satisfied_materials_for_room(client, token: str, room_id: int, enterprise_type: str) -> list[dict]:
    """Uploads a dummy attachment for every material rule required for this
    room/enterprise-type combination and returns the `materials` payload
    ready to submit with a booking — avoids hardcoding assumptions about
    whatever material rules happen to already exist in the (shared, real)
    database."""
    rules = client.get(
        f"/api/enterprise/meeting-rooms/{room_id}/material-rules",
        params={"enterpriseType": enterprise_type},
        headers=auth_headers(token),
    ).json()["data"]
    materials = []
    for rule in rules:
        if rule.get("requiredFlag"):
            att_id = upload_pdf(client, token, filename=f"{rule['materialCode']}.pdf")
            materials.append({"materialCode": rule["materialCode"], "attachmentIds": [att_id]})
    return materials
