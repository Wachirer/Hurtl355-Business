"""
Upload the images/video already in app/static/uploads (and app/static/img) to
your Cloudflare R2 bucket, keeping the same paths the database uses.
Run once after you set the R2_* variables in .env:

    python scripts/upload_media_to_r2.py
"""

import mimetypes
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.utils import r2_enabled, r2_put  # noqa: E402

STATIC = os.path.join(os.path.dirname(__file__), "..", "app", "static")


def main() -> None:
    if not r2_enabled():
        sys.exit("Set all R2_* variables in .env first (see .env.example).")
    count = 0
    for folder in ("uploads", "img"):
        for root, _, files in os.walk(os.path.join(STATIC, folder)):
            for f in files:
                full = os.path.join(root, f)
                key = os.path.relpath(full, STATIC).replace("\\", "/")
                with open(full, "rb") as fh:
                    r2_put(key, fh.read(), mimetypes.guess_type(f)[0])
                print("uploaded", key)
                count += 1
    print(f"Done: {count} files.")


if __name__ == "__main__":
    main()
