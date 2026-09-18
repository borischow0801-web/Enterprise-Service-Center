"""
企业诉求完整业务流程回归测试（B1 §二十八）：

企业注册/登录 → 创建诉求 → 管理端受理 → 退回补充 → 企业补充 → 管理端继续办理
→ 进入评价 → 企业评价 → 管理端办结 → COMPLETED

Verifies the appeal genuinely reaches its terminal state — this is exactly the
flow the module was missing a real "办结" action for before A4.
"""

import secrets

from tests.helpers import admin_login, auth_headers, register_and_login


def test_appeal_reaches_completed_via_full_lifecycle(client):
    region = "R" + secrets.token_hex(3)
    acc = register_and_login(client)
    admin = admin_login(client, region_code=region, role_codes=["CENTER_ADMIN"], data_scope="REGION")

    # 企业提交诉求
    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "全流程测试诉求", "content": "初始内容", "contactName": "甲",
            "contactPhone": "13900000001", "regionCode": region, "regionName": "区域",
        },
    ).json()["data"]
    assert appeal["status"] == "PENDING_ACCEPT"

    # 管理端退回补充
    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/return-supplement",
        headers=auth_headers(admin), json={"opinion": "请补充营业执照"},
    )
    assert r.json()["data"]["status"] == "NEED_SUPPLEMENT"

    # 企业查看详情，能看到退回原因
    detail = client.get(f"/api/enterprise/appeals/{appeal['id']}", headers=auth_headers(acc["token"])).json()["data"]
    assert detail["status"] == "NEED_SUPPLEMENT"
    return_records = [rec for rec in detail["records"] if rec["actionType"] == "RETURN_SUPPLEMENT"]
    assert return_records and return_records[0]["opinion"] == "请补充营业执照"

    # 企业补充材料
    r = client.post(
        f"/api/enterprise/appeals/{appeal['id']}/supplement",
        headers=auth_headers(acc["token"]), json={"content": "已补充营业执照"},
    )
    assert r.json()["data"]["status"] == "PENDING_ACCEPT"

    # 管理端受理 → 企服中心办理
    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/accept",
        headers=auth_headers(admin), json={"appealTypeCode": "T1", "appealTypeName": "测试类型"},
    )
    assert r.json()["data"]["status"] == "ACCEPTED"

    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/center-handle",
        headers=auth_headers(admin), json={"replyContent": "已处理完毕"},
    )
    assert r.json()["data"]["status"] == "PENDING_EVALUATION"

    # 企业评价
    r = client.post(
        f"/api/enterprise/appeals/{appeal['id']}/evaluation",
        headers=auth_headers(acc["token"]),
        json={"satisfaction": "SATISFIED", "score": 5, "resolvedFlag": 1, "comment": "满意"},
    )
    assert r.json()["data"]["status"] == "EVALUATED"

    # 管理端办结 → 终态
    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/complete",
        headers=auth_headers(admin), json={"remark": "已办结"},
    )
    assert r.json()["code"] == 0
    assert r.json()["data"]["status"] == "COMPLETED"

    # 终态后不能重复办结
    r2 = client.post(
        f"/api/admin/appeals/{appeal['id']}/complete",
        headers=auth_headers(admin), json={"remark": "重复办结"},
    )
    assert r2.json()["code"] == 40901


def test_appeal_dept_assignment_flow_reaches_pending_evaluation(client):
    """企服中心 分派责任部门 → 部门反馈 → 企服中心审核通过 的分支路径。"""
    region = "R" + secrets.token_hex(3)
    acc = register_and_login(client)
    admin = admin_login(client, region_code=region, role_codes=["CENTER_ADMIN"], data_scope="REGION")

    appeal = client.post(
        "/api/enterprise/appeals",
        headers=auth_headers(acc["token"]),
        json={
            "title": "分派流程测试诉求", "content": "内容", "contactName": "甲",
            "contactPhone": "13900000001", "regionCode": region, "regionName": "区域",
        },
    ).json()["data"]

    client.post(
        f"/api/admin/appeals/{appeal['id']}/accept",
        headers=auth_headers(admin), json={"appealTypeCode": "T1", "appealTypeName": "测试类型"},
    )
    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/assign",
        headers=auth_headers(admin),
        json={"assignedDeptId": "dept_test", "assignedDeptName": "测试部门", "assignOpinion": "请办理"},
    )
    assert r.json()["data"]["status"] == "DEPT_HANDLING"

    # 部门反馈：DEPT_USER 角色（APPEAL_DEPT_REPLY 权限）也应能提交
    dept_user = admin_login(
        client, region_code=region, role_codes=["DEPT_USER"], data_scope="DEPARTMENT",
        department_id="dept_test",
    )
    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/department-reply",
        headers=auth_headers(dept_user), json={"replyContent": "部门已办理"},
    )
    assert r.json()["code"] == 0
    assert r.json()["data"]["status"] == "CENTER_REVIEWING"

    r = client.post(
        f"/api/admin/appeals/{appeal['id']}/review-reply",
        headers=auth_headers(admin), json={"pass": True, "opinion": "审核通过"},
    )
    assert r.json()["data"]["status"] == "PENDING_EVALUATION"
