from __future__ import annotations

import io
from datetime import timedelta

from minio import Minio

from app.core.config import settings

_client: Minio | None = None
_public_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=f"{settings.MINIO_HOST}:{settings.MINIO_API_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
    return _client


def get_public_minio_client() -> Minio:
    global _public_client
    if _public_client is None:
        endpoint = settings.MINIO_PUBLIC_ENDPOINT or f"localhost:{settings.MINIO_API_PORT}"
        # Strip scheme (http:// or https://) if present in MINIO_PUBLIC_ENDPOINT
        if endpoint.startswith("http://"):
            endpoint = endpoint[7:]
        elif endpoint.startswith("https://"):
            endpoint = endpoint[8:]
            
        _public_client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
            region="us-east-1",
        )
    return _public_client


def ensure_bucket() -> None:
    client = get_minio_client()
    if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
        client.make_bucket(settings.MINIO_BUCKET_NAME)


def upload_object(*, object_path: str, data: bytes, content_type: str) -> None:
    ensure_bucket()
    client = get_minio_client()
    client.put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_path,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def delete_object(object_path: str) -> None:
    client = get_minio_client()
    client.remove_object(settings.MINIO_BUCKET_NAME, object_path)


def get_presigned_download_url(*, object_path: str, expires_seconds: int = 900) -> str:
    ensure_bucket()
    client = get_public_minio_client()
    return client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_path,
        expires=timedelta(seconds=expires_seconds),
    )


def download_object(object_path: str) -> bytes:
    ensure_bucket()
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET_NAME, object_path)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
