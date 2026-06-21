"""Cliente de storage S3-compatível (MinIO no VPS, S3 real depois).

boto3 é síncrono; os serviços async chamam via asyncio.to_thread.
"""
from __future__ import annotations

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket(self, bucket: str) -> None:
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError:
            self.client.create_bucket(Bucket=bucket)
            logger.info(f"Bucket criado: {bucket}")

    def upload_bytes(
        self, bucket: str, key: str, data: bytes, content_type: str | None = None
    ) -> None:
        self.ensure_bucket(bucket)
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=bucket, Key=key, Body=data, **extra)

    def presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
        )

    def public_url(self, bucket: str, key: str) -> str:
        """URL PERMANENTE (não-assinada) do objeto — pro blog público.

        Diferente de ``presigned_url`` (que expira em 1h e não serve pra um post
        que fica no ar), monta ``{base}/{bucket}/{key}`` a partir de
        ``settings.s3_public_url`` (ex.: o MinIO atrás do Caddy). Sem
        ``s3_public_url`` configurado, cai no ``s3_endpoint`` — válido em dev,
        mas em produção o bucket precisa ser de **leitura pública**.
        """
        base = (settings.s3_public_url or settings.s3_endpoint).rstrip("/")
        return f"{base}/{bucket}/{key.lstrip('/')}"


_storage: S3Storage | None = None


def get_storage() -> S3Storage:
    """Singleton do cliente S3 (reaproveita a conexão)."""
    global _storage
    if _storage is None:
        _storage = S3Storage()
    return _storage
