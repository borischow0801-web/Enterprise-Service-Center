from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", summary="工作台统计概览")
def dashboard_summary(current: dict = Depends(require_permissions(Permission.DASHBOARD_VIEW)), db: Session = Depends(get_db)):
    svc = DashboardService(db)
    data = svc.get_summary(
        data_scope=current.get("data_scope", "ALL"),
        region_code=current.get("region_code", ""),
        dept_id=str(current.get("department_id", "") or ""),
    )
    return success(data=data)
