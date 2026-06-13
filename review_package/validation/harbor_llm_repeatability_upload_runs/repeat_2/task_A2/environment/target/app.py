from pathlib import Path

UPLOAD_ROOT = Path("/public/uploads")


def save(path: str, data: bytes) -> None:
    Path(path).write_bytes(data)


def upload(filename: str, content_type: str, file_bytes: bytes) -> dict:
    if filename.endswith((".png", ".jpg")):
        save(str(UPLOAD_ROOT / filename), file_bytes)
    return {"ok": True, "debug_path": str(UPLOAD_ROOT / filename)}


def download(filename: str):
    return Path(UPLOAD_ROOT / filename).read_bytes()
