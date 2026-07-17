# Lưu trữ file (Object Storage)

**Trạng thái:** 🟢 Đã chốt

## 1. Yêu cầu

- v1 chạy **MinIO local**; tương lai chuyển **AWS S3 hoặc Cloudflare R2** mà **không đổi code** — chỉ đổi config.
- File gồm: video bài giảng, audio đề nghe, audio bài nói của học sinh, ảnh, tài liệu Word/Excel/PowerPoint/PDF, file xuất báo cáo.
- Bảo mật: không public bucket; mọi truy cập qua presigned URL có thời hạn; cách ly theo tenant.

## 2. Storage adapter

Backend chỉ gọi interface `Storage`; driver chọn theo config:

```python
# backend/app/core/storage/base.py
class Storage(Protocol):
    async def presign_upload(self, key: str, content_type: str, max_size: int, expires: int = 600) -> PresignedUpload: ...
    async def presign_download(self, key: str, filename: str | None = None, expires: int = 3600) -> str: ...
    async def delete(self, key: str) -> None: ...
    async def copy(self, src: str, dst: str) -> None: ...
    async def stat(self, key: str) -> FileStat: ...       # size, etag, content_type
```

| Driver    | Ghi chú                                                         |
| --------- | ---------------------------------------------------------------- |
| `minio` | v1 — self-host, S3-compatible                                   |
| `s3`    | AWS S3 — cùng SDK (boto3/aioboto3), khác endpoint/credentials |
| `r2`    | Cloudflare R2 — S3-compatible endpoint                          |

Config: `STORAGE_DRIVER=minio|s3|r2`, `STORAGE_ENDPOINT`, `STORAGE_BUCKET`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`, `STORAGE_REGION`.

> Cả 3 driver đều nói chuyện S3 API nên thực chất là 1 implementation + 3 profile config; interface vẫn giữ để test (driver `memory`) và phòng driver khác sau này.

## 3. Quy ước key

```
tenant/<tenant_id>/<module>/<entity_id>/<uuid>.<ext>     # file của tenant
global/content/<entity_id>/<uuid>.<ext>                  # kho nội dung platform
tmp/<upload_session>/<uuid>.<ext>                        # upload chưa gắn entity, TTL 24h
```

- Không dùng tên file người dùng đặt làm key (tránh path injection); tên gốc lưu trong DB (`files.original_name`).
- Bảng `files` trong DB là nguồn chân lý: `id, tenant_id, key, original_name, content_type, size, checksum, module, entity_id, uploaded_by, created_at, deleted_at`.

## 4. Luồng upload (mọi file đều theo luồng này)

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant O as Object Storage

  C->>A: POST /files/presign {module, entity, content_type, size}
  A->>A: check quyền + quota dung lượng + loại file cho phép
  A-->>C: {upload_url, key, max_size}
  C->>O: PUT file (direct, không qua API)
  C->>A: POST /files/confirm {key}
  A->>O: stat(key) — xác minh size/content_type
  A->>A: ghi bảng files + trừ quota; enqueue job hậu xử lý nếu cần
```

Hậu xử lý qua worker theo loại file:

| Loại                         | Xử lý                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| Video bài giảng             | Transcode HLS nhiều bitrate, sinh thumbnail — phát qua presigned URL từng segment |
| Audio (đề nghe / bài nói) | Chuẩn hóa định dạng (opus/mp3), đo duration                                     |
| Ảnh                          | Resize các cỡ, strip EXIF                                                           |
| Word/Excel/PPT/PDF            | Quét virus (ClamAV), sinh preview PDF trang đầu (nếu bật)                        |

## 5. Download & phát nội dung

- Mọi download qua `GET /files/{id}/url` → API check quyền (đúng tenant, đúng vai trò, học sinh phải nằm trong assignment chứa file...) → trả presigned URL 1 giờ.
- Video: trả presigned playlist HLS; không hỗ trợ tải toàn bộ video bài giảng (chống rò rỉ nội dung — mức chống copy v1 dừng ở đây, DRM để v2).
- File đính kèm bài học (Word/Excel/PPT): học sinh tải bản gốc.

## 6. Quota & dọn dẹp

- Quota dung lượng theo gói tenant ([SRS Gói dịch vụ](../14-goi-dich-vu/srs-goi-dich-vu.md)); upload vượt → 402 kèm thông báo rõ.
- `tmp/` quá 24h chưa confirm → xóa (cron).
- Soft-delete: `deleted_at` 30 ngày → xóa vật lý khỏi storage.
- Retention audio học sinh theo cấu hình tenant (mặc định 24 tháng — [Bảo mật](03-bao-mat.md)).

## 7. Câu hỏi mở cần chốt

| # | Câu hỏi                                                                          | Quyết định                                                              | Ngày chốt |
| - | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ----------- |
| 1 | Transcode HLS ngay v1 hay v1 chỉ phát MP4 progressive (đơn giản hơn nhiều)? | **Chốt:** v1 phát MP4 progressive; HLS khi có nhu cầu video dài | 2026-07-16  |
| 2 | Giới hạn kích thước video tối đa (đề xuất 2GB/file)?                     | **Chốt:** 2GB/file                                                  | 2026-07-16  |

## Lịch sử thay đổi

| Ngày      | Thay đổi                                                                                     | Người         |
| ---------- | ---------------------------------------------------------------------------------------------- | --------------- |
| 2026-07-16 | Tạo bản nháp đầu tiên                                                                    | Claude          |
| 2026-07-16 | Chốt toàn bộ câu hỏi mở (quyết định ghi trong bảng), chuyển trạng thái Đã chốt | Chủ sản phẩm |
