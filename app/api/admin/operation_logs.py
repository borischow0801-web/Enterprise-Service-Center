from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.core.response import paginated
from app.models.system import SysOperationLog

router = APIRouter()


def _to_dict(log: SysOperationLog) -> dict:
    return {
        "id": log.id,
        "operatorType": log.operator_type,
        "operatorId": log.operator_id,
        "operatorName": log.operator_name,
        "businessType": log.business_type,
        "businessId": log.business_id,
        "operationType": log.operation_type,
        "operationContent": log.operation_content,
        "beforeStatus": log.before_status,
        "afterStatus": log.after_status,
        "ipAddress": log.ip_address,
        "userAgent": log.user_agent,
        "createdAt": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("", summary="操作日志分页查询")
def list_operation_logs(
    current: CurrentAdmin,
    db: Session = Depends(get_db),
    operatorType: Optional[str] = Query(None),
    operatorName: Optional[str] = Query(None),
    businessType: Optional[str] = Query(None),
    operationType: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
):
    q = db.query(SysOperationLog)
    if operatorType:
        q = q.filter(SysOperationLog.operator_type == operatorType)
    if operatorName:
        q = q.filter(SysOperationLog.operator_name.contains(operatorName))
    if businessType:
        q = q.filter(SysOperationLog.business_type == businessType)
    if operationType:
        q = q.filter(SysOperationLog.operation_type.contains(operationType))
    if startDate:
        q = q.filter(SysOperationLog.created_at >= datetime.strptime(startDate, "%Y-%m-%d"))
    if endDate:
        q = q.filter(SysOperationLog.created_at <= datetime.strptime(f"{endDate} 23:59:59", "%Y-%m-%d %H:%M:%S"))

    total = q.count()
    records = (
        q.order_by(SysOperationLog.created_at.desc())
        .offset((pageNo - 1) * pageSize)
        .limit(pageSize)
        .all()
    )
    return paginated(
        records=[_to_dict(r) for r in records],
        total=total,
        page_no=pageNo,
        page_size=pageSize,
    )
