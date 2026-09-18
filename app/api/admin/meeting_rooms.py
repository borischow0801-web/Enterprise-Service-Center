from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.schemas.meeting_room import (
    RoomCreateRequest, RoomUpdateRequest, RoomStatusRequest,
    OpenRulesRequest, SpecialDateRequest, OccupyRequest,
    MaterialRuleCreateRequest, MaterialRuleUpdateRequest,
)
from app.services.meeting_room_service import MeetingRoomService

router = APIRouter()


def _op(current: dict) -> dict:
    return {
        "operator_type": "USER",
        "operator_id": str(current.get("user_id", current.get("platform_user_id", ""))),
        "operator_name": current.get("real_name", ""),
        "department_id": current.get("department_id"),
        "department_name": current.get("department_name"),
        "data_scope": current.get("data_scope"),
        "region_code": current.get("region_code"),
        "role_codes": current.get("role_codes"),
    }


# ── 静态路由（必须在 /{room_id} 之前，避免路由冲突）─────────────────────────

@router.get("", summary="会议室管理列表（管理端）")
def list_rooms(
    current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)),
    db: Session = Depends(get_db),
    regionCode: Optional[str] = Query(None),
    serviceCenterId: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    roomType: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = MeetingRoomService(db)
    total, records = svc.list_rooms_admin(
        {"regionCode": regionCode, "serviceCenterId": serviceCenterId, "status": status,
         "roomType": roomType, "pageNo": pageNo, "pageSize": pageSize},
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.post("", summary="新增会议室")
def create_room(body: RoomCreateRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.create_room(body.model_dump(), _op(current))
    return success(data=result, message="会议室创建成功")


@router.post("/special-dates", summary="配置特殊日期")
def create_special_date(body: SpecialDateRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.create_special_date(body.model_dump(), _op(current))
    return success(data=result)


@router.post("/occupies", summary="手工占用会议室")
def create_occupy(body: OccupyRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.create_occupy(body.model_dump(), _op(current))
    return success(data=result)


@router.get("/material-rules", summary="材料规则列表")
def list_material_rules(
    current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)),
    db: Session = Depends(get_db),
    regionCode: Optional[str] = Query(None),
    serviceCenterId: Optional[int] = Query(None),
    roomId: Optional[int] = Query(None),
    enterpriseType: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
):
    svc = MeetingRoomService(db)
    return success(data=svc.list_material_rules(
        region_code=regionCode, service_center_id=serviceCenterId,
        room_id=roomId, enterprise_type=enterpriseType, enabled=enabled,
    ))


@router.post("/material-rules", summary="新增材料规则")
def create_material_rule(body: MaterialRuleCreateRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.create_material_rule(body.model_dump(), _op(current))
    return success(data=result)


@router.put("/material-rules/{rule_id}", summary="修改材料规则")
def update_material_rule(rule_id: int, body: MaterialRuleUpdateRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.update_material_rule(rule_id, body.model_dump(exclude_unset=True), _op(current))
    return success(data=result)


@router.delete("/material-rules/{rule_id}", summary="删除材料规则")
def delete_material_rule(rule_id: int, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    svc.delete_material_rule(rule_id, _op(current))
    return success(message="删除成功")


# ── 动态路由（/{room_id} 必须在所有静态路由之后）────────────────────────────

@router.get("/{room_id}", summary="会议室详情（管理端）")
def get_room_detail(room_id: int, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    return success(data=svc.get_room_detail_enterprise(room_id))


@router.put("/{room_id}", summary="修改会议室")
def update_room(room_id: int, body: RoomUpdateRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.update_room(room_id, body.model_dump(exclude_unset=True), _op(current))
    return success(data=result, message="修改成功")


@router.patch("/{room_id}/status", summary="启用/停用会议室")
def set_room_status(room_id: int, body: RoomStatusRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.set_room_status(room_id, body.status, _op(current))
    return success(data=result)


@router.get("/{room_id}/open-rules", summary="获取开放规则")
def get_open_rules(room_id: int, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    rules = svc.repo.get_open_rules(room_id)
    return success(data={
        "roomId": room_id,
        "rules": [
            {
                "weekday": r.weekday,
                "openFlag": r.open_flag,
                "startTime": r.start_time,
                "endTime": r.end_time,
            }
            for r in rules
        ]
    })


@router.put("/{room_id}/open-rules", summary="配置开放规则")
def set_open_rules(room_id: int, body: OpenRulesRequest, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_MANAGE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.set_open_rules(room_id, [r.model_dump() for r in body.rules], _op(current))
    return success(data=result)
