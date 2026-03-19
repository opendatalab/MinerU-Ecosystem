from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Image:
    """An image extracted from the document."""

    name: str
    data: bytes
    path: str  # relative path inside the zip, e.g. "images/img_0.png"

    def save(self, filepath: str) -> Path:
        """Save image to *filepath*, creating parent directories as needed."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self.data)
        return p


@dataclass
class Progress:
    """Extraction progress for a running task."""

    extracted_pages: int
    total_pages: int
    start_time: str

    @property
    def percent(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return self.extracted_pages / self.total_pages * 100

    def __str__(self) -> str:
        return f"{self.extracted_pages}/{self.total_pages} ({self.percent:.0f}%)"


@dataclass
class ExtractResult:
    """Result of a document extraction task.

    When ``state == "done"``, content fields (``markdown``, ``content_list``,
    ``images``, and any requested extra formats) are populated.
    When the task is still in progress, only metadata and ``progress`` are set.
    """

    task_id: str
    state: str  # "done" | "failed" | "pending" | "running" | "converting"
    filename: str | None = None
    err_code: str = ""
    error: str | None = None
    zip_url: str | None = None

    progress: Progress | None = None

    markdown: str | None = None
    content_list: list[dict] | None = None
    images: list[Image] = field(default_factory=list)

    docx: bytes | None = None
    html: str | None = None
    latex: str | None = None

    _zip_bytes: bytes | None = field(default=None, repr=False)

    # ── save helpers ──

    def save_markdown(self, path: str, with_images: bool = True) -> Path:
        """Save markdown file. When *with_images* is True, write an ``images/``
        directory alongside the markdown file."""
        if self.markdown is None:
            raise ValueError("No markdown content available (state != done)")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.markdown, encoding="utf-8")
        if with_images and self.images:
            img_dir = p.parent / "images"
            img_dir.mkdir(exist_ok=True)
            for img in self.images:
                (img_dir / img.name).write_bytes(img.data)
        return p

    def save_docx(self, path: str) -> Path:
        """Save docx file."""
        if self.docx is None:
            raise ValueError("No docx content available")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self.docx)
        return p

    def save_html(self, path: str) -> Path:
        """Save html file."""
        if self.html is None:
            raise ValueError("No html content available")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.html, encoding="utf-8")
        return p

    def save_latex(self, path: str) -> Path:
        """Save latex file."""
        if self.latex is None:
            raise ValueError("No latex content available")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.latex, encoding="utf-8")
        return p

    def save_all(self, dir: str) -> Path:
        """Extract the full result zip to *dir*."""
        if self._zip_bytes is None:
            raise ValueError("No zip data available (state != done)")
        import zipfile
        import io

        d = Path(dir)
        d.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(self._zip_bytes)) as zf:
            zf.extractall(d)
        return d
