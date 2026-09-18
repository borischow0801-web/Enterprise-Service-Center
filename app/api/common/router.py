import os
import re
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
from app.core.exceptions import NotLoginException, FileUploadException, NotFoundException
from app.models.system import SysAttachment, SysDictionary
from app.services.attachment_access_service import (
    assert_attachment_accessible,
    is_public_reference_asset,
    BUSINESS_TYPE_TEMP,
)
from sqlalchemy.orm import Session

router = APIRouter()

# ── Upload safety ────────────────────────────────────────────────────────────
# 白名单覆盖三大模块目前实际用到的材料类型：申请表/证明材料（文档）与图片。
# 不收录任何可执行/脚本/网页类型，也不做 zip 等归档格式（本系统业务不需要）。
_ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}

# 客户端声明的 Content-Type 一旦命中以下前缀，无论扩展名是什么一律拒绝——
# 防止把可执行/网页/脚本内容伪装成图片或文档扩展名上传（上传后若被匿名/跨权限下载并
# 被浏览器直接渲染，可构成存储型 XSS 或本地代码执行诱导）。
_DANGEROUS_CONTENT_TYPE_PREFIXES = (
    "text/html",
    "application/javascript",
    "text/javascript",
    "application/x-msdownload",
    "application/x-executable",
    "application/x-sh",
    "application/x-php",
    "application/x-httpd-php",
    "application/x-msdos-program",
)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def _sanitize_original_name(filename: str) -> str:
    """去掉路径分量和控制字符；不信任客户端原始文件名用于任何文件系统操作
    （存储路径始终使用服务端生成的 UUID，这里只是让展示用的文件名干净、安全）。"""
    name = os.path.basename((filename or "").strip()) or "unknown"
    name = _CONTROL_CHARS_RE.sub("", name)
    return name[:255] or "unknown"


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


def _get_authenticated_caller(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    """Accept both enterprise and admin tokens (upload + download share this gate)."""
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
    payload: dict = Depends(_get_authenticated_caller),
):
    # 文件大小限制在读取全部内容之前先按声明的 Content-Length 做一次快速拒绝，
    # 减少恶意超大请求体在被拒绝前占用的内存；读取后仍会再校验一次实际字节数
    # （部分客户端不发送准确的 Content-Length，不能只信这一层）。
    declared_size = file.size if file.size is not None else None
    if declared_size is not None and declared_size > settings.max_upload_size:
        raise FileUploadException(
            f"文件超过最大限制 {settings.max_upload_size // 1024 // 1024}MB"
        )

    original_name = _sanitize_original_name(file.filename)
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise FileUploadException(
            "不支持的文件类型，仅支持：" + "、".join(sorted(e.lstrip(".") for e in _ALLOWED_EXTENSIONS))
        )
    if file.content_type and file.content_type.lower().startswith(_DANGEROUS_CONTENT_TYPE_PREFIXES):
        raise FileUploadException("文件类型不受支持")

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise FileUploadException(
            f"文件超过最大限制 {settings.max_upload_size // 1024 // 1024}MB"
        )
    if len(content) == 0:
        raise FileUploadException("文件内容为空")

    token_type = payload.get("token_type", "enterprise")
    if token_type == "enterprise":
        uploader_type = "ENTERPRISE"
        uploader_id = str(payload.get("enterprise_id", ""))
        uploader_name = payload.get("enterprise_name", "")
    else:
        uploader_type = "USER"
        uploader_id = str(payload.get("user_id", payload.get("platform_user_id", "")))
        uploader_name = payload.get("real_name", "")

    # 存储文件名始终由服务端生成的 UUID + 白名单扩展名拼接，不使用客户端原始文件名，
    # 从根本上避免路径穿越；original_name 只用于展示/下载时的文件名。
    stored_name = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(settings.upload_dir_resolved, "attachments")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, stored_name)
    if os.path.dirname(os.path.abspath(save_path)) != os.path.abspath(save_dir):
        # 防御性校验：理论上 stored_name 恒为 "<uuid hex><白名单扩展名>"，不可能跳出 save_dir，
        # 这里只是不信任假设本身，保留一道兜底。
        raise FileUploadException("文件保存路径非法")

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
        mime_type=_ALLOWED_EXTENSIONS[ext],
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
        "downloadUrl": f"/api/common/attachments/{attachment.id}/download",
    }, message="上传成功")


@router.get("/attachments/{attachment_id}/download", summary="下载/预览附件（业务附件需登录并按归属与数据权限校验；会议室公开展示图片/材料模板除外）")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
):
    att = db.query(SysAttachment).filter(
        SysAttachment.id == attachment_id,
        SysAttachment.deleted_flag == 0,
    ).first()
    if not att:
        raise NotFoundException("附件不存在")

    # 会议室封面/图册/材料模板是面向所有企业公开展示的浏览内容（<img> 标签无法携带
    # Authorization 头），本来就不属于"业务敏感附件"，维持匿名可访问；
    # 其余一切业务附件（诉求/预约/政企约见材料、未绑定的临时上传）必须登录并通过归属校验。
    if not (att.business_type == BUSINESS_TYPE_TEMP and is_public_reference_asset(db, att.id)):
        if credentials is None:
            raise NotLoginException()
        try:
            payload = decode_token(credentials.credentials)
        except JWTError:
            raise NotLoginException("token 无效或已过期")
        assert_attachment_accessible(db, att, payload)

    if not os.path.exists(att.storage_path):
        raise NotFoundException("文件不存在")

    # media_type 由服务端根据扩展名白名单派生，不信任存量数据里可能残留的客户端声明值。
    ext = os.path.splitext(att.storage_path)[1].lower()
    media_type = _ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")
    return FileResponse(
        path=att.storage_path,
        filename=att.original_name,
        media_type=media_type,
    )
