"""
Shared utility functions: file uploads (local or Cloudflare R2), validation,
rate-limiting.

Storage modes
-------------
* Local (default): files are written to app/static/uploads/... — fine for
  development, but hosts like Render wipe the disk on every redeploy/restart.
* Cloudflare R2 (production): set the R2_* variables and every upload goes to
  the bucket instead. The database always stores the same relative key
  (e.g. "uploads/images/abc.png"), so switching modes needs no data changes.
"""

import io
import mimetypes
import os
import time
import uuid
from collections import defaultdict
from functools import wraps
from typing import Tuple

from flask import current_app, request, jsonify, url_for
from PIL import Image
from werkzeug.utils import secure_filename

# ── In-memory rate limit store (per endpoint key) ─────────────────────────────
# Structure: { key: [timestamp, ...] }
# NOTE: this lives in process memory, so run gunicorn with ONE worker
# (render.yaml already does) or move this to Redis if you scale out.
_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate(key: str, max_calls: int, period_seconds: int = 3600) -> bool:
    """Record a hit for `key`; return False if it is over the limit."""
    now = time.time()
    window = [t for t in _rate_store[key] if now - t < period_seconds]
    if len(window) >= max_calls:
        _rate_store[key] = window
        return False
    window.append(now)
    _rate_store[key] = window
    return True


def rate_limited(max_calls: int, period_seconds: int = 3600):
    """Decorator: reject if the client IP exceeds max_calls in period_seconds."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or "unknown"
            if not check_rate(f"{fn.__name__}:{ip}", max_calls, period_seconds):
                return jsonify({"error": "Too many requests. Please try again later."}), 429
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ── Cloudflare R2 (S3-compatible) ─────────────────────────────────────────────

_R2_VARS = ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_URL")
_r2_client = None


def r2_enabled() -> bool:
    return all(os.getenv(v) for v in _R2_VARS)


def _r2():
    """Lazily build the boto3 client (boto3 is only imported when R2 is used)."""
    global _r2_client
    if _r2_client is None:
        import boto3

        _r2_client = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
    return _r2_client


def r2_put(key: str, data: bytes, content_type: str | None = None) -> None:
    _r2().put_object(
        Bucket=os.environ["R2_BUCKET"],
        Key=key,
        Body=data,
        ContentType=content_type or mimetypes.guess_type(key)[0] or "application/octet-stream",
        CacheControl="public, max-age=31536000, immutable",
    )


def r2_delete(key: str) -> None:
    _r2().delete_object(Bucket=os.environ["R2_BUCKET"], Key=key)


def media_url(path: str | None) -> str:
    """Public URL for a stored media path (works in Jinja templates)."""
    if not path:
        return ""
    if path.startswith(("http://", "https://")):
        return path
    if r2_enabled():
        return f"{os.environ['R2_PUBLIC_URL'].rstrip('/')}/{path.lstrip('/')}"
    return url_for("static", filename=path)


# ── File helpers ───────────────────────────────────────────────────────────────

def _looks_valid(ext: str, head: bytes) -> bool:
    """Check the file's first bytes match its extension (don't trust names alone)."""
    if ext in ("jpg", "jpeg"):
        return head[:3] == b"\xff\xd8\xff"
    if ext == "png":
        return head[:8] == b"\x89PNG\r\n\x1a\n"
    if ext == "webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if ext == "mp3":
        return head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)
    if ext == "wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if ext == "mp4":
        return head[4:8] == b"ftyp"
    return False


def _content_ok(file_storage) -> bool:
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    head = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    return _looks_valid(ext, head)


def allowed_file(filename: str, extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


def unique_filename(original: str) -> str:
    """Return a UUID-prefixed secure filename."""
    ext = original.rsplit(".", 1)[-1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def _rel_key(upload_dir: str, fname: str) -> str:
    """Path of upload_dir/fname relative to static/, with forward slashes."""
    dest = os.path.join(upload_dir, fname)
    return os.path.relpath(dest, current_app.static_folder).replace("\\", "/")


def save_upload(file_storage, upload_dir: str, extensions: set[str]) -> Tuple[bool, str]:
    """
    Validate and save an uploaded FileStorage object.

    Returns (success, relative_path_from_static_or_error_message).
    The relative path is the same whether the file lands on disk or in R2.
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename, extensions):
        return False, f"File type not allowed. Allowed: {', '.join(sorted(extensions))}"

    if not _content_ok(file_storage):
        return False, "That file's contents do not match its extension."

    fname = unique_filename(secure_filename(file_storage.filename))
    rel = _rel_key(upload_dir, fname)

    if r2_enabled():
        r2_put(rel, file_storage.read())  # content type comes from the extension, not the client
        return True, rel

    os.makedirs(upload_dir, exist_ok=True)
    file_storage.save(os.path.join(upload_dir, fname))
    return True, rel


_PIL_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}


def save_image_with_thumbnail(
    file_storage,
    upload_dir: str,
    thumb_dir: str,
    thumb_size: Tuple[int, int] = (600, 400),
) -> Tuple[bool, str, str]:
    """
    Save an image and generate a thumbnail.

    Returns (success, rel_image_path, rel_thumb_path).
    """
    extensions = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]

    if r2_enabled():
        if not file_storage or file_storage.filename == "":
            return False, "No file selected.", ""
        if not allowed_file(file_storage.filename, extensions):
            return False, f"File type not allowed. Allowed: {', '.join(sorted(extensions))}", ""

        if not _content_ok(file_storage):
            return False, "That file's contents do not match its extension.", ""

        fname = unique_filename(secure_filename(file_storage.filename))
        ext = fname.rsplit(".", 1)[-1]
        data = file_storage.read()
        rel = _rel_key(upload_dir, fname)
        r2_put(rel, data)

        rel_thumb = rel
        try:
            with Image.open(io.BytesIO(data)) as img:
                img = img.convert("RGB")
                img.thumbnail(thumb_size, Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format=_PIL_FORMATS.get(ext, "JPEG"), optimize=True, quality=85)
            rel_thumb = _rel_key(thumb_dir, f"thumb_{fname}")
            r2_put(rel_thumb, buf.getvalue())
        except Exception:
            rel_thumb = rel  # fall back to the original
        return True, rel, rel_thumb

    ok, result = save_upload(file_storage, upload_dir, extensions)
    if not ok:
        return False, result, ""

    # Generate thumbnail with Pillow
    static_folder = current_app.static_folder
    full_path = os.path.join(static_folder, result)
    os.makedirs(thumb_dir, exist_ok=True)

    fname = os.path.basename(full_path)
    thumb_path = os.path.join(thumb_dir, f"thumb_{fname}")

    try:
        with Image.open(full_path) as img:
            img = img.convert("RGB")
            img.thumbnail(thumb_size, Image.LANCZOS)
            img.save(thumb_path, optimize=True, quality=85)
        rel_thumb = os.path.relpath(thumb_path, static_folder).replace("\\", "/")
    except Exception:
        rel_thumb = result  # fall back to original

    return True, result, rel_thumb


def delete_static_file(rel_path: str) -> None:
    """Delete a stored file given its static/-relative path (disk or R2)."""
    if not rel_path:
        return
    if r2_enabled():
        try:
            r2_delete(rel_path)
        except Exception:
            current_app.logger.warning("Could not delete %s from R2", rel_path)
        return
    full = os.path.join(current_app.static_folder, rel_path)
    if os.path.isfile(full):
        os.remove(full)
