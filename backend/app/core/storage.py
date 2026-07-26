"""Storage adapter cho file media (audio…). Xem docs/01-kien-truc/04-luu-tru-file.md.

MinIO local trước, đổi S3/R2 chỉ bằng config (cùng giao thức S3). MemoryStorage cho test
(không cần container MinIO). Key LUÔN có prefix "{tenant_id}/" — tầng API kiểm tra prefix
để chặn đọc chéo tenant.
"""

from typing import Protocol

from app.config import settings


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> tuple[bytes, str]: ...  # (bytes, content_type); KeyError nếu thiếu


class MemoryStorage:
    """Lưu trong RAM — chỉ dùng cho test."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[bytes, str]] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._data[key] = (data, content_type)

    def get(self, key: str) -> tuple[bytes, str]:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]


class MinioStorage:
    def __init__(self) -> None:
        from minio import Minio

        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        import io

        self._client.put_object(
            self._bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
        )

    def get(self, key: str) -> tuple[bytes, str]:
        from minio.error import S3Error

        try:
            resp = self._client.get_object(self._bucket, key)
            try:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "application/octet-stream")
            finally:
                resp.close()
                resp.release_conn()
            return data, ctype
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket"):
                raise KeyError(key) from None
            raise


_instance: Storage | None = None


def get_storage() -> Storage:
    global _instance
    if _instance is None:
        _instance = MemoryStorage() if settings.storage_backend == "memory" else MinioStorage()
    return _instance


def use_memory_storage() -> MemoryStorage:
    """Cho test: thay singleton bằng MemoryStorage mới."""
    global _instance
    _instance = MemoryStorage()
    return _instance
