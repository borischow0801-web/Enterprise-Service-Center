import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from jose import JWTError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.core.response import success
from app.core.exceptions import NotLoginException, FileUploadException
from app.models.system import SysAttachment, SysDictionary
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/dictionaries/{dict_type}", summary="通用字典查询（无需登录）")
def get_dict_by_type(dict_type: str, db: Session = Depends(get_db)):
    """返回指定 dictType 下所有启用的字典项，按 sort_no 升序。企业端和管理端都可调用。"""
    items = (
        db.query(SysDictionary)
        .filter(
            SysDictionary.dict_type == dict_type,
            SysDictionary.enabled == 1,
            SysDictionary.deleted_flag == 0,
        )
        .order_by(SysDictionary.sort_no)
        .all()
    )
    return success(data=[
        {
            "id": item.id,
            "dictType": item.dict_type,
            "dictCode": item.dict_code,
            "dictLabel": item.dict_label,
            "dictValue": item.dict_value,
            "sortNo": item.sort_no,
            "parentCode": item.parent_code,
        }
        for item in items
    ])
_bearer = HTTPBearer(auto_error=False)


def _get_uploader(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    """Accept both enterprise and admin tokens for file uploads."""
    if credentials is None:
        raise NotLoginException()
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise NotLoginException("token 无效或已过期")
    return payload


@router.get("/health", summary="健康检查")
async def health_check():
    return success(data={"status": "ok"})


@router.post("/attachments/upload", summary="上传附件（支持企业端和管理端token）")
async def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(_get_uploader),
):
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise FileUploadException(
            f"文件超过最大限制 {settings.max_upload_size // 1024 // 1024}MB"
        )

    token_type = payload.get("token_type", "enterprise")
    if token_type == "enterprise":
        uploader_type = "ENTERPRISE"
        uploader_id = str(payload.get("enterprise_id", ""))
        uploader_name = payload.get("enterprise_name", "")
    else:
        uploader_type = "USER"
        uploader_id = str(payload.get("user_id", payload.get("platform_user_id", "")))
        uploader_name = payload.get("real_name", "")

    original_name = file.filename or "unknown"
    ext = os.path.splitext(original_name)[1].lower() or ".bin"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(settings.upload_dir_resolved, "attachments")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, stored_name)

    try:
        with open(save_path, "wb") as f:
            f.write(content)
    except OSError as e:
        err_msg = str(e)
        if "Permission denied" in err_msg or getattr(e, "errno", None) == 13:
            raise FileUploadException(
                "文件上传失败：上传目录无写权限，请检查 uploads 目录权限（参见 docs/UPLOADS_PERMISSION_FIX.md）"
            )
        raise FileUploadException(f"文件保存失败: {err_msg}")

    attachment = SysAttachment(
        business_type="TEMP",
        business_id=None,
        file_category=None,
        original_name=original_name,
        stored_name=stored_name,
        file_ext=ext.lstrip("."),
        mime_type=file.content_type,
        file_size=len(content),
        storage_path=save_path,
        uploaded_by_type=uploader_type,
        uploaded_by_id=uploader_id,
        uploaded_by_name=uploader_name,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return success(data={
        "id": attachment.id,
        "originalName": attachment.original_name,
        "fileExt": attachment.file_ext,
        "fileSize": attachment.file_size,
        "storagePath": attachment.storage_path,
        "downloadUrl": f"/api/common/attachments/{attachment.id}/download",
    }, message="上传成功")


@router.get("/attachments/{attachment_id}/download", summary="下载/预览附件")
def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    att = db.query(SysAttachment).filter(
        SysAttachment.id == attachment_id,
        SysAttachment.deleted_flag == 0,
    ).first()
    if not att:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="附件不存在")
    if not os.path.exists(att.storage_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=att.storage_path,
        filename=att.original_name,
        media_type=att.mime_type or "application/octet-stream",
    )
