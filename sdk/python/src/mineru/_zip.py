"""Download and parse MinerU result zip files."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import PurePosixPath

from .models import ExtractResult, Image


def parse_zip(zip_bytes: bytes, task_id: str, filename: str | None = None) -> ExtractResult:
    """Parse a MinerU result zip into an ExtractResult with all fields populated."""
    markdown: str | None = None
    content_list: list[dict] | None = None
    images: list[Image] = []
    docx: bytes | None = None
    html: str | None = None
    latex: str | None = None

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue

            name = PurePosixPath(info.filename).name
            suffix = PurePosixPath(name).suffix.lower()
            rel_path = info.filename

            data = zf.read(info.filename)

            if suffix == ".md":
                markdown = data.decode("utf-8")
            elif name.endswith("_content_list.json") or name == "content_list.json":
                content_list = json.loads(data)
            elif suffix == ".json" and content_list is None:
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, list):
                        content_list = parsed
                except (json.JSONDecodeError, ValueError):
                    pass
            elif suffix in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"):
                images.append(Image(name=name, data=data, path=rel_path))
            elif suffix == ".docx":
                docx = data
            elif suffix == ".html" or suffix == ".htm":
                html = data.decode("utf-8")
            elif suffix == ".tex":
                latex = data.decode("utf-8")

    return ExtractResult(
        task_id=task_id,
        state="done",
        filename=filename,
        zip_url=None,
        markdown=markdown,
        content_list=content_list,
        images=images,
        docx=docx,
        html=html,
        latex=latex,
        _zip_bytes=zip_bytes,
    )
