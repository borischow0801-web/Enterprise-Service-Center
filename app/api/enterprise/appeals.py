from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import CurrentEnterprise
from app.core.response import success, paginated
from app.schemas.appeal import (
    AppealSubmitRequest,
    AppealModifyRequest,
    AppealSupplementRequest,
    AppealEvaluationRequest,
)
from app.services.appeal_service import AppealService

router = APIRouter()


@router.post("", summary="提交诉求")
def submit_appeal(
    body: AppealSubmitRequest,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    data = body.model_dump()
    result = svc.submit_appeal(current["enterprise_id"], data)
    return success(data=result, message="诉求提交成功")


@router.get("", summary="我的诉求列表")
def list_appeals(
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = AppealService(db)
    total, records = svc.list_enterprise_appeals(
        enterprise_id=current["enterprise_id"],
        status=status,
        page_no=pageNo,
        page_size=pageSize,
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/{appeal_id}", summary="诉求详情")
def get_appeal_detail(
    appeal_id: int,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    result = svc.get_appeal_detail_for_enterprise(appeal_id, current["enterprise_id"])
    return success(data=result)


@router.put("/{appeal_id}", summary="修改诉求")
def modify_appeal(
    appeal_id: int,
    body: AppealModifyRequest,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    result = svc.modify_appeal(appeal_id, current["enterprise_id"], body.model_dump(exclude_none=True))
    return success(data=result, message="修改成功")


@router.post("/{appeal_id}/supplement", summary="补充材料")
def supplement_appeal(
    appeal_id: int,
    body: AppealSupplementRequest,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    result = svc.supplement_appeal(appeal_id, current["enterprise_id"], body.model_dump())
    return success(data=result, message="材料补充成功")


@router.post("/{appeal_id}/evaluation", summary="企业评价诉求")
def evaluate_appeal(
    appeal_id: int,
    body: AppealEvaluationRequest,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    result = svc.evaluate_appeal(appeal_id, current["enterprise_id"], body.model_dump())
    return success(data=result, message="评价成功")
