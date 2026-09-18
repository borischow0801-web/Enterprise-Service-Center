"""
政企约见核心流程回归测试（B1 §三十）：

企业申请 → 管理端审核 → 安排 → 确认 → 完成 → 评价 → 办结 → 验证 COMPLETED。
"""

import secrets

from tests.helpers import admin_login, auth_headers, register_and_login, unique_credit_code


def test_gov_meeting_reaches_completed_via_full_lifecycle(client):
    region = "R" + secrets.token_hex(3)
    acc = register_and_login(client)
    admin = admin_login(client, region_code=region, role_codes=["CENTER_ADMIN"], data_scope="REGION")

    apply_ = client.post(
        "/api/enterprise/gov-meetings",
        headers=auth_headers(acc["token"]),
        json={
            "enterpriseName": "政企约见流程测试企业", "creditCode": unique_credit_code(),
            "contactName": "甲", "contactPhone": "13900000001", "registeredAddress": "测试地址",
            "industryName": "测试行业", "title": "政企约见流程测试", "meetingContent": "内容",
            "discussionItem": "洽谈事项", "urgencyLevel": "NORMAL",
            "regionCode": region, "regionName": "区域", "commitmentChecked": 1,
        },
    ).json()["data"]
    assert apply_["status"] == "PENDING_AUDIT"

    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/audit",
        headers=auth_headers(admin), json={"auditType": "ACCEPT", "opinion": "同意受理"},
    )
    assert r.json()["data"]["status"] == "PENDING_ARRANGE"

    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/arrange",
        headers=auth_headers(admin),
        json={
            "meetingDate": "2099-03-01T09:00:00", "meetingPlace": "会议室A",
            "meetingMethod": "ON_SITE", "hostDeptId": "d1", "hostDeptName": "企服中心",
        },
    )
    assert r.json()["code"] == 0, r.text  # 返回的是约见安排记录，不是申请本身
    detail = client.get(f"/api/admin/gov-meetings/{apply_['id']}", headers=auth_headers(admin)).json()["data"]
    assert detail["status"] == "ARRANGED"

    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/confirm",
        headers=auth_headers(admin), json={},
    )
    assert r.json()["data"]["status"] == "WAIT_MEETING"

    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/complete",
        headers=auth_headers(admin), json={},
    )
    assert r.json()["data"]["status"] == "MEETING_COMPLETED"

    # 填写纪要，自动触发进入待评价
    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/record",
        headers=auth_headers(admin), json={"content": "约见纪要内容", "conclusions": "达成一致"},
    )
    assert r.json()["code"] == 0
    detail = client.get(f"/api/admin/gov-meetings/{apply_['id']}", headers=auth_headers(admin)).json()["data"]
    assert detail["status"] == "PENDING_EVALUATION"

    # 企业评价
    r = client.post(
        f"/api/enterprise/gov-meetings/{apply_['id']}/evaluate",
        headers=auth_headers(acc["token"]),
        json={"satisfaction": "SATISFIED", "score": 5, "resolvedFlag": 1, "comment": "满意"},
    )
    assert r.json()["data"]["status"] == "EVALUATED"

    # 管理端办结 → 终态
    r = client.post(
        f"/api/admin/gov-meetings/{apply_['id']}/finish",
        headers=auth_headers(admin), json={},
    )
    assert r.json()["code"] == 0
    assert r.json()["data"]["status"] == "COMPLETED"
