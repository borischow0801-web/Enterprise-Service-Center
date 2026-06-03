from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import CurrentEnterprise
from app.core.response import success, paginated
from app.schemas.gov_meeting import (
    GovMeetingSubmitRequest, GovMeetingModifyRequest,
    GovMeetingSupplementRequest, GovMeetingEvaluationRequest,
)
from app.services.gov_meeting_service import GovMeetingService

router = APIRouter()


@router.post("", summary="提交政企约见申请")
def submit_apply(body: GovMeetingSubmitRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.submit_apply(current["enterprise_id"], body.model_dump())
    return success(data=result, message="申请提交成功")


@router.get("", summary="我的政企约见列表")
def list_applies(
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = GovMeetingService(db)
    total, records = svc.list_applies_enterprise(
        current["enterprise_id"],
        {"status": status, "pageNo": pageNo, "pageSize": pageSize},
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/notice", summary="政企约见须知")
def get_notice():
    """企业端约见须知（静态文本，正式环境可改为 CMS/字典配置）"""
    return success(
        data={
            "content": (
                "1. 企业可通过本平台提交政企约见申请，请如实填写企业信息、约见主题与期望层级。\n"
                "2. 提交后由企业综合服务中心受理审核，审核通过后将安排具体约见时间、地点及参会人员。\n"
                "3. 约见完成后，企业可对本次服务进行评价。\n"
                "4. 如有疑问，请联系属地企业综合服务中心。"
            ),
        }
    )


@router.get("/{apply_id}", summary="政企约见详情（企业端）")
def get_apply_detail(apply_id: int, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    return success(data=svc.get_apply_detail_enterprise(current["enterprise_id"], apply_id))


@router.put("/{apply_id}", summary="修改政企约见申请")
def modify_apply(apply_id: int, body: GovMeetingModifyRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.modify_apply(current["enterprise_id"], apply_id, body.model_dump(exclude_none=True))
    return success(data=result, message="修改成功")


@router.post("/{apply_id}/supplement", summary="补充材料")
def supplement_apply(apply_id: int, body: GovMeetingSupplementRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.supplement_apply(current["enterprise_id"], apply_id, body.model_dump(exclude_none=True))
    return success(data=result, message="补充材料提交成功")


@router.post("/{apply_id}/evaluate", summary="评价政企约见")
def evaluate_apply(apply_id: int, body: GovMeetingEvaluationRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.evaluate_apply(current["enterprise_id"], apply_id, body.model_dump())
    return success(data=result, message="评价成功")
