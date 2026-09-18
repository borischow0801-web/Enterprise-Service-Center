"""
Authorization regression tests (B1 §二十七 focus):越权测试 must be as prominent
as happy-path tests. Covers cross-region data-scope enforcement (A2) and
role-permission enforcement (A3) across Appeal / Meeting Room / Gov Meeting,
plus the attachment access rules built in A1.
"""

import secrets

from tests.helpers import (
    admin_login,
    auth_headers,
    register_and_login,
    satisfied_materials_for_room,
    unique_credit_code,
)


def _region() -> str:
    return "R" + secrets.token_hex(3)


# ── Appeal ───────────────────────────────────────────────────────────────────

def test_region_admin_cannot_access_other_region_appeal(client):
    region_a, region_b = _region(), _region()
    acc = register_and_login(client)
    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "越权测试诉求", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region_a, "regionName": "区域A",
        },
    ).json()["data"]

    admin_b = admin_login(client, region_code=region_b, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    resp = client.get(f"/api/admin/appeals/{appeal['id']}", headers=auth_headers(admin_b))
    assert resp.json()["code"] == 40301

    admin_a = admin_login(client, region_code=region_a, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    ok = client.get(f"/api/admin/appeals/{appeal['id']}", headers=auth_headers(admin_a))
    assert ok.json()["code"] == 0


def test_region_admin_cannot_accept_other_region_appeal(client):
    region_a, region_b = _region(), _region()
    acc = register_and_login(client)
    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "越权受理测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region_a, "regionName": "区域A",
        },
    ).json()["data"]

    admin_b = admin_login(client, region_code=region_b, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    resp = client.post(
        f"/api/admin/appeals/{appeal['id']}/accept",
        headers=auth_headers(admin_b),
        json={"appealTypeCode": "T1", "appealTypeName": "测试类型"},
    )
    assert resp.json()["code"] == 40301


def test_role_without_appeal_permission_cannot_act(client):
    region = _region()
    acc = register_and_login(client)
    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "无角色权限测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region, "regionName": "区域",
        },
    ).json()["data"]

    room_admin = admin_login(client, region_code=region, role_codes=["ROOM_ADMIN"], data_scope="REGION")
    resp = client.post(
        f"/api/admin/appeals/{appeal['id']}/accept",
        headers=auth_headers(room_admin),
        json={"appealTypeCode": "T1", "appealTypeName": "测试类型"},
    )
    assert resp.json()["code"] == 40301


def test_no_role_admin_cannot_view_dashboard(client):
    admin = admin_login(client, region_code=_region(), role_codes=[], data_scope="ALL")
    resp = client.get("/api/admin/dashboard/summary", headers=auth_headers(admin))
    assert resp.json()["code"] == 40301


def test_unknown_data_scope_fails_closed(client):
    """未知 data_scope 必须拒绝而不是默认放行为 ALL。"""
    region = _region()
    acc = register_and_login(client)
    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "未知数据范围测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region, "regionName": "区域",
        },
    ).json()["data"]

    admin_unknown_scope = admin_login(
        client, region_code=region, role_codes=["CENTER_ADMIN"], data_scope="SOME_UNRECOGNIZED_SCOPE"
    )
    resp = client.get(f"/api/admin/appeals/{appeal['id']}", headers=auth_headers(admin_unknown_scope))
    assert resp.json()["code"] == 40301

    list_resp = client.get("/api/admin/appeals?pageSize=5", headers=auth_headers(admin_unknown_scope))
    assert list_resp.json()["data"]["total"] == 0


# ── Meeting Room ─────────────────────────────────────────────────────────────

def test_region_admin_cannot_access_other_region_booking(client):
    region_a, region_b = _region(), _region()
    room_admin_a = admin_login(client, region_code=region_a, role_codes=["ROOM_ADMIN"], data_scope="REGION")
    room = client.post(
        "/api/admin/meeting-rooms",
        headers=auth_headers(room_admin_a),
        json={"roomName": "越权测试会议室", "regionCode": region_a, "regionName": "区域A", "capacity": 10},
    ).json()["data"]

    acc = register_and_login(client)
    materials = satisfied_materials_for_room(client, acc["token"], room["id"], "OTHER")
    booking_resp = client.post(
        "/api/enterprise/meeting-bookings",
        headers=auth_headers(acc["token"]),
        json={
            "roomId": room["id"], "meetingSubject": "越权测试会议", "participantCount": 3,
            "contactName": "甲", "contactPhone": "13900000001",
            "startTime": "2099-01-08 09:00:00", "endTime": "2099-01-08 10:00:00",
            "enterpriseType": "OTHER", "enterpriseTypeName": "其他", "materials": materials,
        },
    )
    assert booking_resp.json()["code"] == 0, booking_resp.text
    booking = booking_resp.json()["data"]

    room_admin_b = admin_login(client, region_code=region_b, role_codes=["ROOM_ADMIN"], data_scope="REGION")
    resp = client.get(f"/api/admin/meeting-bookings/{booking['id']}", headers=auth_headers(room_admin_b))
    assert resp.json()["code"] == 40301

    approve_resp = client.post(
        f"/api/admin/meeting-bookings/{booking['id']}/approve",
        headers=auth_headers(room_admin_b),
        json={},
    )
    assert approve_resp.json()["code"] == 40301


def test_role_without_room_manage_permission_cannot_create_room(client):
    region = _region()
    center_staff = admin_login(client, region_code=region, role_codes=["CENTER_STAFF"], data_scope="REGION")
    resp = client.post(
        "/api/admin/meeting-rooms",
        headers=auth_headers(center_staff),
        json={"roomName": "无权限新增测试", "regionCode": region, "regionName": "区域", "capacity": 5},
    )
    assert resp.json()["code"] == 40301


# ── Gov Meeting ──────────────────────────────────────────────────────────────

def test_region_admin_cannot_access_other_region_gov_meeting(client):
    region_a, region_b = _region(), _region()
    acc = register_and_login(client)
    apply_ = client.post(
        "/api/enterprise/gov-meetings",
        headers=auth_headers(acc["token"]),
        json={
            "enterpriseName": "越权约见测试企业", "creditCode": unique_credit_code(),
            "contactName": "甲", "contactPhone": "13900000001", "registeredAddress": "测试地址",
            "industryName": "测试行业", "title": "越权约见测试", "meetingContent": "内容",
            "discussionItem": "事项", "urgencyLevel": "NORMAL",
            "regionCode": region_a, "regionName": "区域A", "commitmentChecked": 1,
        },
    ).json()["data"]

    admin_b = admin_login(client, region_code=region_b, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    resp = client.get(f"/api/admin/gov-meetings/{apply_['id']}", headers=auth_headers(admin_b))
    assert resp.json()["code"] == 40301

    admin_a = admin_login(client, region_code=region_a, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    ok = client.get(f"/api/admin/gov-meetings/{apply_['id']}", headers=auth_headers(admin_a))
    assert ok.json()["code"] == 0


# ── Attachments (§三十一) ─────────────────────────────────────────────────────

def _upload_pdf(client, token: str) -> int:
    resp = client.post(
        "/api/common/attachments/upload",
        headers=auth_headers(token),
        files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
    )
    assert resp.json()["code"] == 0, resp.text
    return resp.json()["data"]["id"]


def test_anonymous_cannot_download_attachment(client):
    acc = register_and_login(client)
    att_id = _upload_pdf(client, acc["token"])
    resp = client.get(f"/api/common/attachments/{att_id}/download")
    assert resp.json()["code"] == 40101


def test_enterprise_can_download_own_unbound_attachment(client):
    acc = register_and_login(client)
    att_id = _upload_pdf(client, acc["token"])
    resp = client.get(f"/api/common/attachments/{att_id}/download", headers=auth_headers(acc["token"]))
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_enterprise_b_cannot_download_enterprise_a_bound_attachment(client):
    region = _region()
    acc_a = register_and_login(client)
    acc_b = register_and_login(client)
    att_id = _upload_pdf(client, acc_a["token"])

    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc_a["token"]),
        json={
            "title": "附件越权测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region, "regionName": "区域", "attachmentIds": [att_id],
        },
    ).json()["data"]
    assert appeal["id"]

    resp = client.get(f"/api/common/attachments/{att_id}/download", headers=auth_headers(acc_b["token"]))
    assert resp.json()["code"] == 40301

    own = client.get(f"/api/common/attachments/{att_id}/download", headers=auth_headers(acc_a["token"]))
    assert own.status_code == 200


def test_admin_with_permission_and_scope_can_download_appeal_attachment(client):
    region = _region()
    acc = register_and_login(client)
    att_id = _upload_pdf(client, acc["token"])
    client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "管理端下载测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region, "regionName": "区域", "attachmentIds": [att_id],
        },
    )
    admin = admin_login(client, region_code=region, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    resp = client.get(f"/api/common/attachments/{att_id}/download", headers=auth_headers(admin))
    assert resp.status_code == 200


def test_admin_without_data_scope_cannot_download_appeal_attachment(client):
    region_a, region_b = _region(), _region()
    acc = register_and_login(client)
    att_id = _upload_pdf(client, acc["token"])
    client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "管理端越权下载测试", "content": "内容", "contactName": "甲", "contactPhone": "13900000001",
            "regionCode": region_a, "regionName": "区域A", "attachmentIds": [att_id],
        },
    )
    admin_wrong_region = admin_login(client, region_code=region_b, role_codes=["CENTER_ADMIN"], data_scope="REGION")
    resp = client.get(f"/api/common/attachments/{att_id}/download", headers=auth_headers(admin_wrong_region))
    assert resp.json()["code"] == 40301


def test_illegal_file_type_upload_rejected(client):
    acc = register_and_login(client)
    resp = client.post(
        "/api/common/attachments/upload",
        headers=auth_headers(acc["token"]),
        files={"file": ("malware.exe", b"MZ fake exe content", "application/x-msdownload")},
    )
    assert resp.json()["code"] == 50003


def test_legal_file_upload_succeeds(client):
    acc = register_and_login(client)
    att_id = _upload_pdf(client, acc["token"])
    assert att_id
