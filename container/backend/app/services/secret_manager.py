from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException

from app.config import settings


@lru_cache(maxsize=32)
def _read_secret(secret_name: str) -> str:
    if not secret_name.strip():
        return ""
    if not settings.gcp_project_id.strip():
        raise HTTPException(status_code=503, detail="GCP_PROJECT_ID neni nakonfigurovany.")

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    path = f"projects/{settings.gcp_project_id.strip()}/secrets/{secret_name.strip()}/versions/latest"
    response = client.access_secret_version(request={"name": path})
    return response.payload.data.decode("utf-8").strip()


def resolve_value(direct_value: str, secret_name: str) -> str:
    value = (direct_value or "").strip()
    if value:
        return value
    return _read_secret(secret_name)
