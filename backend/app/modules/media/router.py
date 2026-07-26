"""Upload + phát file media (audio câu hỏi nghe/nói). Key namespaced theo tenant.
Upload: vai trò soạn nội dung. Phát: mọi người dùng đã đăng nhập CÙNG tenant
(kiểm prefix key — không đọc chéo tenant được dù đoán ra key).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from app.core.authn import CurrentUser, get_current_user
from app.core.storage import get_storage

router = APIRouter(prefix="/api/v1/media", tags=["media"])

_UPLOAD_ROLES = {"owner", "manager", "academic_head", "teacher", "content_editor"}
_MAX_BYTES = 15 * 1024 * 1024  # 15MB đủ cho audio nghe vài phút
_ALLOWED = {
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/webm": "webm",
}


@router.post("", status_code=201)
async def upload_media(
    file: UploadFile,
    current: CurrentUser = Depends(get_current_user),
):
    if current.role not in _UPLOAD_ROLES:
        raise HTTPException(403, "forbidden_role")
    ctype = (file.content_type or "").split(";")[0].strip()
    if ctype not in _ALLOWED:
        raise HTTPException(422, f"unsupported_type:{ctype}")
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "file_too_large_max_15mb")
    if not data:
        raise HTTPException(422, "empty_file")
    key = f"{current.tenant_id}/{uuid.uuid4()}.{_ALLOWED[ctype]}"
    get_storage().put(key, data, ctype)
    return {"key": key, "content_type": ctype, "size": len(data)}


@router.get("/{key:path}")
async def get_media(
    key: str,
    current: CurrentUser = Depends(get_current_user),
):
    # chặn path traversal + đọc chéo tenant: key phải đúng namespace tenant của mình
    if ".." in key or not key.startswith(f"{current.tenant_id}/"):
        raise HTTPException(403, "not_your_media")
    try:
        data, ctype = get_storage().get(key)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    return Response(
        content=data,
        media_type=ctype,
        headers={"Cache-Control": "private, max-age=3600"},
    )
