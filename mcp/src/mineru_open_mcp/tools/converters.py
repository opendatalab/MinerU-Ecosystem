"""File conversion logic for MinerU MCP tools."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config
from ..language import resolve_language


def _log_sdk_call(method: str, **kwargs) -> None:
    """Log SDK call arguments in a readable format."""
    config.logger.info(
        "Calling %s:\n%s",
        method,
        "\n".join(f"  {k}: {v!r}" for k, v in kwargs.items()),
    )


def _normalize_extra_formats(
    extra_formats: Optional[List[str]],
) -> Optional[List[str]]:
    """Expand ``"all"`` → individual formats and deduplicate.

    Returns a sorted list of SDK-valid format strings, or None if empty.
    """
    if not extra_formats:
        return None
    valid = {"docx", "html", "latex"}
    expanded: set = set()
    for f in extra_formats:
        if f == "all":
            expanded |= valid
        elif f in valid:
            expanded.add(f)
    return sorted(expanded) or None


def _build_error_entries(sources: List[str], error_msg: str) -> List[Dict[str, Any]]:
    """Build a per-source error list from a single SDK-level error."""
    return [
        {"filename": _source_filename(s), "status": "error", "error": error_msg}
        for s in sources
    ]


def _unique_stem(stem: str, used_stems: set) -> str:
    """Return stem unchanged if unused, otherwise append _1, _2, … until unique."""
    if stem not in used_stems:
        return stem
    counter = 1
    while f"{stem}_{counter}" in used_stems:
        counter += 1
    return f"{stem}_{counter}"


def _save_extra_formats(
    result: Any,
    stem_dir: Path,
    stem: str,
    filename: str,
    sdk_formats: Optional[List[str]],
) -> Dict[str, str]:
    """Save extra output formats (docx/html/latex) alongside the Markdown file."""
    if not sdk_formats:
        return {}
    fmt_ext = {"docx": ".docx", "html": ".html", "latex": ".tex"}
    fmt_save = {"docx": result.save_docx, "html": result.save_html, "latex": result.save_latex}
    saved: Dict[str, str] = {}
    for fmt in sdk_formats:
        if getattr(result, fmt, None) is None:
            continue
        fmt_path = stem_dir / f"{stem}{fmt_ext[fmt]}"
        try:
            fmt_save[fmt](str(fmt_path))
            saved[fmt] = str(fmt_path)
        except Exception as e:
            config.logger.warning(f"保存 {fmt} 文件时出错 ({filename}): {e}")
    return saved


async def _build_result_entry(
    result: Any,
    filename: str,
    stem: str,
    out_dir: Path,
    sdk_formats: Optional[List[str]],
    ctx: Any,
) -> Dict[str, Any]:
    """Convert one SDK ExtractResult into a result dict entry."""
    if result.state == "failed":
        if ctx:
            await ctx.warning(f"解析失败: {filename} — {result.error}")
        return {"filename": filename, "status": "error",
                "error": result.error or "服务端解析失败"}

    if result.markdown is None:
        return {"filename": filename, "status": "error",
                "error": "任务完成但未返回 Markdown 内容"}

    stem_dir = out_dir / stem
    md_path = stem_dir / f"{stem}.md"
    try:
        result.save_markdown(str(md_path), with_images=True)
        extract_path = str(stem_dir)
    except Exception as e:
        config.logger.warning(f"保存 Markdown 文件时出错 ({filename}): {e}")
        extract_path = str(out_dir)

    entry: Dict[str, Any] = {
        "filename": filename, "status": "success",
        "content": result.markdown, "extract_path": extract_path,
    }
    if result.zip_url:
        entry["zip_url"] = result.zip_url
    saved_formats = _save_extra_formats(result, stem_dir, stem, filename, sdk_formats)
    if saved_formats:
        entry["saved_formats"] = saved_formats
    if ctx:
        await ctx.info(f"解析完成: {filename} → {extract_path}")
    return entry


async def convert_sources(
    sources: List[str],
    enable_ocr: bool = False,
    language: str = "Chinese",
    model: Optional[str] = None,
    page_ranges_map: Optional[Dict[int, str]] = None,
    output_dir: str = config.DEFAULT_OUTPUT_DIR,
    ctx=None,
    token: Optional[str] = None,
    extra_formats: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Convert a mixed list of local file paths and/or URLs to Markdown via the MinerU SDK.

    Runs the synchronous SDK in a thread-pool executor so the MCP async layer is not blocked.
    Saves each result's Markdown (and images) under *output_dir* and returns per-file result dicts.

    Args:
        language: Document language name (e.g. ``"Chinese"``, ``"Korean"``, ``"Macedonian"``).
            Resolved to the SDK prefix code via ``resolve_language()``.
            Defaults to ``"Chinese"``.
        model: Parsing model — ``"vlm"``, ``"pipeline"``, ``"html"``, or ``None`` (default, auto-inferred by SDK).
            Use ``"pipeline"`` only for documents in uncommon languages not well supported by vlm.
            Use ``"html"`` for web page extraction.
            Ignored in Flash mode.
        token: Optional per-request MinerU API token. Falls back to config.MINERU_TOKEN if not given.
        extra_formats: Optional list of additional output formats to generate alongside Markdown.
            Accepted values: "docx", "html", "latex", "all" (all three).
            Not available in Flash mode (markdown only). Saved next to the Markdown file.
        page_ranges_map: Optional dict mapping 0-based index into *sources* to a page-range
            string (e.g. ``{0: "1-3", 2: "5,7"}``).
            Sources without an entry are extracted in full.
            Passed to ``extract_batch()`` via the ``file_params`` argument as a
            ``{source: FileParam(pages=range)}`` dict.

    Returns a list, one entry per source:
        success: {"filename": str, "source": str, "status": "success",
                  "content": "<markdown>", "extract_path": str,
                  "saved_formats": {"docx": "<path>", ...}}
        failed:  {"filename": str, "source": str, "status": "error",
                  "error_message": str}
    """
    from mineru.client import FileParam, MinerU
    from mineru.exceptions import MinerUError

    if not sources:
        return []

    token = token or config.MINERU_TOKEN
    use_flash = not token
    sdk_formats = _normalize_extra_formats(extra_formats)
    lang = resolve_language(language)
    sdk_model = model or None
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def _run_sync() -> list:
        with MinerU(token=token or None) as client:
            if use_flash:
                results = []
                for i, s in enumerate(sources):
                    page_range = page_ranges_map.get(i) if page_ranges_map else None
                    _log_sdk_call("client.flash_extract",
                                  source=s, language=lang, page_range=page_range)
                    results.append(client.flash_extract(s, language=lang, page_range=page_range))
                return results
            fp = {
                sources[i]: FileParam(pages=pr)
                for i, pr in page_ranges_map.items()
                if i < len(sources)
            } if page_ranges_map else None
            _log_sdk_call("client.extract_batch", sources=sources, model=sdk_model,
                          ocr=enable_ocr, language=lang, extra_formats=sdk_formats,
                          file_params=fp)
            return list(client.extract_batch(sources, model=sdk_model, ocr=enable_ocr,
                                             language=lang, extra_formats=sdk_formats,
                                             file_params=fp))

    if ctx:
        if use_flash:
            await ctx.info(
                f"未检测到 API Token，使用 Flash 模式处理 {len(sources)} 个文件/URL "
                f"(仅输出 Markdown，最大 20 页 / 10 MB)… | "
                f"No API token — using Flash mode (markdown only, 20 pages / 10 MB limit)."
            )
            if sdk_formats:
                await ctx.warning(
                    "Flash 模式不支持额外输出格式，已忽略 extra_formats 参数。 | "
                    "Flash mode does not support extra formats (markdown only); extra_formats ignored."
                )
        else:
            await ctx.info(f"使用 MinerU SDK 处理 {len(sources)} 个文件/URL…")

    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _run_sync)
    except MinerUError as e:
        if ctx:
            await ctx.error(f"SDK 调用失败: {e}")
        return _build_error_entries(sources, str(e))
    except Exception as e:
        if ctx:
            await ctx.error(f"处理文件时发生异常: {e}")
        return _build_error_entries(sources, str(e))

    processed: List[Dict[str, Any]] = []
    used_stems: set = set()
    for i, result in enumerate(results):
        source = sources[i] if i < len(sources) else ""
        filename = result.filename or _source_filename(source)
        stem = _unique_stem(Path(filename).stem, used_stems)
        used_stems.add(stem)
        entry = await _build_result_entry(result, filename, stem,
                                          out_dir, sdk_formats, ctx)
        processed.append(entry)
    return processed


def _source_filename(source: str) -> str:
    """Derive a display filename from a path or URL."""
    if source.startswith(("http://", "https://")):
        name = source.split("?")[0].split("/")[-1]
        return name or source
    return Path(source).name
