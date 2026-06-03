from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.core.response import success, paginated
from app.core.exceptions import AppException, NotFoundException
from app.models.system import SysDictionary, SysOperationLog
from app.constants.dictionary import (
    MAINTAINABLE_DICT_TYPES,
    DICT_NOT_MAINTAINABLE_MSG,
    is_maintainable_dict_type,
)
from datetime import datetime

router = APIRouter()


def _to_dict(item: SysDictionary) -> dict:
    return {
        "id": item.id,
        "dictType": item.dict_type,
        "dictCode": item.dict_code,
        "dictLabel": item.dict_label,
        "dictValue": item.dict_value,
        "sortNo": item.sort_no,
        "enabled": item.enabled,
        "parentCode": item.parent_code,
        "extraJson": item.extra_json,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
    }


def _assert_maintainable(dict_type: str) -> None:
    if not is_maintainable_dict_type(dict_type):
        raise AppException(40301, DICT_NOT_MAINTAINABLE_MSG)


def _write_op_log(db: Session, current: dict, op_type: str, dict_type: str,
                  dict_code: str, dict_label: str = ""):
    label_part = f"「{dict_label}」" if dict_label else ""
    content = f"字典类型={dict_type}，编码={dict_code}{label_part}，操作={op_type}"
    log = SysOperationLog(
        operator_type="USER",
        operator_id=str(current.get("user_id", "")),
        operator_name=current.get("real_name", ""),
        business_type="DICT",
        operation_type=op_type,
        operation_content=content,
    )
    db.add(log)


@router.get("", summary="字典分页列表（仅可维护类型）")
def list_dictionaries(
    current: CurrentAdmin,
    db: Session = Depends(get_db),
    dictType: Optional[str] = Query(None),
    dictCode: Optional[str] = Query(None),
    dictLabel: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
):
    if dictType and not is_maintainable_dict_type(dictType):
        return paginated(records=[], total=0, page_no=pageNo, page_size=pageSize)

    q = db.query(SysDictionary).filter(
        SysDictionary.deleted_flag == 0,
        SysDictionary.dict_type.in_(MAINTAINABLE_DICT_TYPES),
    )
    if dictType:
        q = q.filter(SysDictionary.dict_type == dictType)
    if dictCode:
        q = q.filter(SysDictionary.dict_code.contains(dictCode))
    if dictLabel:
        q = q.filter(SysDictionary.dict_label.contains(dictLabel))
    if enabled is not None:
        q = q.filter(SysDictionary.enabled == enabled)
    total = q.count()
    records = q.order_by(SysDictionary.sort_no, SysDictionary.id)\
               .offset((pageNo - 1) * pageSize).limit(pageSize).all()
    return paginated(records=[_to_dict(r) for r in records], total=total, page_no=pageNo, page_size=pageSize)


@router.post("", summary="新增字典")
def create_dictionary(
    body: dict,
    current: CurrentAdmin,
    db: Session = Depends(get_db),
):
    dict_type = body.get("dictType") or ""
    dict_code = body.get("dictCode") or ""
    dict_label = body.get("dictLabel") or ""
    if not dict_type or not dict_code:
        raise AppException(40001, "dictType 和 dictCode 不能为空")

    _assert_maintainable(dict_type)

    exists = db.query(SysDictionary).filter(
        SysDictionary.dict_type == dict_type,
        SysDictionary.dict_code == dict_code,
        SysDictionary.deleted_flag == 0,
    ).first()
    if exists:
        raise AppException(40001, f"字典 {dict_type}.{dict_code} 已存在")

    item = SysDictionary(
        dict_type=dict_type,
        dict_code=dict_code,
        dict_label=dict_label,
        dict_value=body.get("dictValue"),
        sort_no=body.get("sortNo", 0),
        enabled=body.get("enabled", 1),
        parent_code=body.get("parentCode"),
        extra_json=body.get("extraJson"),
    )
    db.add(item)
    _write_op_log(db, current, "DICT_CREATE", dict_type, dict_code, dict_label)
    db.commit()
    db.refresh(item)
    return success(data=_to_dict(item), message="新增成功")


@router.put("/{dict_id}", summary="修改字典")
def update_dictionary(
    dict_id: int,
    body: dict,
    current: CurrentAdmin,
    db: Session = Depends(get_db),
):
    item = db.query(SysDictionary).filter(
        SysDictionary.id == dict_id, SysDictionary.deleted_flag == 0
    ).first()
    if not item:
        raise NotFoundException("字典不存在")

    _assert_maintainable(item.dict_type)

    if "dictType" in body and body["dictType"] != item.dict_type:
        raise AppException(40001, "不允许修改字典类型")

    new_code = body.get("dictCode", item.dict_code)
    if new_code != item.dict_code:
        dup = db.query(SysDictionary).filter(
            SysDictionary.dict_type == item.dict_type,
            SysDictionary.dict_code == new_code,
            SysDictionary.deleted_flag == 0,
            SysDictionary.id != dict_id,
        ).first()
        if dup:
            raise AppException(40001, f"字典 {item.dict_type}.{new_code} 已存在")

    for field, col in [("dictCode", "dict_code"), ("dictLabel", "dict_label"),
                       ("dictValue", "dict_value"), ("sortNo", "sort_no"),
                       ("parentCode", "parent_code"), ("extraJson", "extra_json")]:
        if field in body:
            setattr(item, col, body[field])
    if "enabled" in body:
        item.enabled = body["enabled"]

    item.updated_at = datetime.utcnow()
    _write_op_log(db, current, "DICT_UPDATE", item.dict_type, item.dict_code, item.dict_label)
    db.commit()
    db.refresh(item)
    return success(data=_to_dict(item), message="修改成功")


@router.patch("/{dict_id}/status", summary="启用/停用字典")
def toggle_dictionary_status(
    dict_id: int,
    body: dict,
    current: CurrentAdmin,
    db: Session = Depends(get_db),
):
    item = db.query(SysDictionary).filter(
        SysDictionary.id == dict_id, SysDictionary.deleted_flag == 0
    ).first()
    if not item:
        raise NotFoundException("字典不存在")

    _assert_maintainable(item.dict_type)

    enabled = body.get("enabled", item.enabled)
    item.enabled = enabled
    item.updated_at = datetime.utcnow()
    op = "DICT_ENABLE" if enabled else "DICT_DISABLE"
    _write_op_log(db, current, op, item.dict_type, item.dict_code, item.dict_label)
    db.commit()
    return success(data=_to_dict(item), message="操作成功")
