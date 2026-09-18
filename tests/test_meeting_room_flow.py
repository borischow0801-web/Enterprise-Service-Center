"""
共享会议室核心流程回归测试（B1 §二十九）：

企业提交预约 → 管理端审核 → APPROVED → COMPLETED，外加一个非法状态操作测试
（不要求本轮解决 TOCTOU 并发竞态问题，只验证状态机本身拒绝非法跳转）。
"""

import secrets

from tests.helpers import admin_login, auth_headers, register_and_login, satisfied_materials_for_room


def _region() -> str:
    return "R" + secrets.token_hex(3)


def test_booking_reaches_completed(client):
    region = _region()
    room_admin = admin_login(client, region_code=region, role_codes=["ROOM_ADMIN"], data_scope="REGION")
    room = client.post(
        "/api/admin/meeting-rooms",
        headers=auth_headers(room_admin),
        json={"roomName": "流程测试会议室", "regionCode": region, "regionName": "区域", "capacity": 10},
    ).json()["data"]

    acc = register_and_login(client)
    materials = satisfied_materials_for_room(client, acc["token"], room["id"], "OTHER")
    booking = client.post(
        "/api/enterprise/meeting-bookings",
        headers=auth_headers(acc["token"]),
        json={
            "roomId": room["id"], "meetingSubject": "流程测试会议", "participantCount": 5,
            "contactName": "甲", "contactPhone": "13900000001",
            "startTime": "2099-02-10 09:00:00", "endTime": "2099-02-10 10:00:00",
            "enterpriseType": "OTHER", "enterpriseTypeName": "其他", "materials": materials,
        },
    ).json()["data"]
    assert booking["status"] == "PENDING_AUDIT"

    r = client.post(
        f"/api/admin/meeting-bookings/{booking['id']}/approve",
        headers=auth_headers(room_admin), json={"auditOpinion": "同意"},
    )
    assert r.json()["data"]["status"] == "APPROVED"

    r = client.post(
        f"/api/admin/meeting-bookings/{booking['id']}/complete",
        headers=auth_headers(room_admin), json={"remark": "使用完毕"},
    )
    assert r.json()["code"] == 0
    assert r.json()["data"]["status"] == "COMPLETED"


def test_illegal_state_transition_rejected(client):
    """已完成的预约不能再次被驳回——状态机必须拒绝非法跳转。"""
    region = _region()
    room_admin = admin_login(client, region_code=region, role_codes=["ROOM_ADMIN"], data_scope="REGION")
    room = client.post(
        "/api/admin/meeting-rooms",
        headers=auth_headers(room_admin),
        json={"roomName": "非法跳转测试会议室", "regionCode": region, "regionName": "区域", "capacity": 10},
    ).json()["data"]

    acc = register_and_login(client)
    materials = satisfied_materials_for_room(client, acc["token"], room["id"], "OTHER")
    booking = client.post(
        "/api/enterprise/meeting-bookings",
        headers=auth_headers(acc["token"]),
        json={
            "roomId": room["id"], "meetingSubject": "非法跳转测试", "participantCount": 2,
            "contactName": "甲", "contactPhone": "13900000001",
            "startTime": "2099-02-11 09:00:00", "endTime": "2099-02-11 10:00:00",
            "enterpriseType": "OTHER", "enterpriseTypeName": "其他", "materials": materials,
        },
    ).json()["data"]

    client.post(f"/api/admin/meeting-bookings/{booking['id']}/approve", headers=auth_headers(room_admin), json={})
    client.post(f"/api/admin/meeting-bookings/{booking['id']}/complete", headers=auth_headers(room_admin), json={})

    # 已 COMPLETED，再驳回应被状态机拒绝（40901），而不是静默成功产生脏状态
    r = client.post(
        f"/api/admin/meeting-bookings/{booking['id']}/reject",
        headers=auth_headers(room_admin), json={"auditOpinion": "尝试非法驳回"},
    )
    assert r.json()["code"] == 40901
