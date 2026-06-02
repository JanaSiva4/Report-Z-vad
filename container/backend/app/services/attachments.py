from __future__ import annotations

import base64
from datetime import timedelta
import re
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.config import settings


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}
LOCAL_TEST_PREFIX = "tickets_test_"
LOCAL_ATTACHMENT_DIR = Path(__file__).resolve().parents[2] / ".local_test_store" / "attachments"


def _is_local_test_store() -> bool:
    return (
        settings.firestore_collection.strip().startswith(LOCAL_TEST_PREFIX)
        or settings.firestore_collection.strip() == ""
        or str(settings.firestore_collection).startswith(LOCAL_TEST_PREFIX)
    )


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return cleaned[:140] or "priloha"


def _decode_data_url(value: str) -> tuple[bytes, str]:
    if "," not in value:
        raise HTTPException(status_code=400, detail="Priloha nema platny format.")
    header, encoded = value.split(",", 1)
    content_type = "application/octet-stream"
    match = re.match(r"data:([^;]+);base64", header)
    if match:
        content_type = match.group(1)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Priloha musi byt JPG, PNG nebo PDF.")
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Prilohu se nepodarilo nacist.") from exc
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=400, detail="Priloha je vetsi nez 10 MB.")
    return content, content_type


def store_ticket_attachments(ticket_id: str, attachments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not attachments:
        return []

    stored: list[dict[str, Any]] = []

    if _is_local_test_store():
        ticket_dir = LOCAL_ATTACHMENT_DIR / ticket_id
        ticket_dir.mkdir(parents=True, exist_ok=True)
        for index, attachment in enumerate(attachments, start=1):
            original_name = str(attachment.get("name") or f"priloha-{index}")
            content, content_type = _decode_data_url(str(attachment.get("data") or ""))
            filename = _safe_filename(original_name)
            object_name = f"{index:02d}-{filename}"
            file_path = ticket_dir / object_name
            file_path.write_bytes(content)
            stored.append(
                {
                    "name": original_name,
                    "content_type": content_type,
                    "size": len(content),
                    "bucket": "",
                    "object": object_name,
                    "local_path": str(file_path),
                    "gcs_uri": "",
                }
            )
        return stored

    if not settings.gcs_bucket:
        raise HTTPException(status_code=503, detail="GCS_BUCKET neni nakonfigurovany pro ukladani priloh.")

    from google.cloud import storage

    client = storage.Client(project=settings.gcp_project_id or None)
    bucket = client.bucket(settings.gcs_bucket)

    for index, attachment in enumerate(attachments, start=1):
        original_name = str(attachment.get("name") or f"priloha-{index}")
        content, content_type = _decode_data_url(str(attachment.get("data") or ""))
        filename = _safe_filename(original_name)
        object_name = f"tickets/{ticket_id}/{index:02d}-{filename}"
        blob = bucket.blob(object_name)
        blob.upload_from_string(content, content_type=content_type)
        stored.append(
            {
                "name": original_name,
                "content_type": content_type,
                "size": len(content),
                "bucket": settings.gcs_bucket,
                "object": object_name,
                "gcs_uri": f"gs://{settings.gcs_bucket}/{object_name}",
            }
        )
    return stored


def signed_attachment_url(attachment: dict[str, Any]) -> str:
    local_path = str(attachment.get("local_path") or "")
    if local_path:
        return local_path

    bucket_name = str(attachment.get("bucket") or settings.gcs_bucket)
    object_name = str(attachment.get("object") or "")
    if not bucket_name or not object_name:
        raise HTTPException(status_code=404, detail="Priloha nema ulozenou cestu.")

    from google.cloud import storage

    client = storage.Client(project=settings.gcp_project_id or None)
    blob = client.bucket(bucket_name).blob(object_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET",
    )


def delete_stored_attachments(attachments: list[dict[str, Any]]) -> None:
    if not attachments:
        return

    local_mode = _is_local_test_store()
    for attachment in attachments:
        local_path = str(attachment.get("local_path") or "")
        if local_mode and local_path:
            Path(local_path).unlink(missing_ok=True)
            continue

        bucket_name = str(attachment.get("bucket") or settings.gcs_bucket)
        object_name = str(attachment.get("object") or "")
        if not bucket_name or not object_name:
            continue

        from google.api_core.exceptions import NotFound
        from google.cloud import storage

        client = storage.Client(project=settings.gcp_project_id or None)
        try:
            client.bucket(bucket_name).blob(object_name).delete()
        except NotFound:
            continue
