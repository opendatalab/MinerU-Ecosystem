"""File extraction logic for MinerU MCP tools."""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .. import config

_FLASH_PAGE_RANGE_RE = re.compile(r"^\d+(-\d+)?$")


def _sanitize_flash_page_range(page_range: str) -> Optional[str]:
    """Return page_range if valid for Flash mode, else None."""
    value = page_range.strip()
    return value if _FLASH_PAGE_RANGE_RE.match(value) else None


def _log_sdk_call(method: str, **kwargs) -> None:
    """Log SDK call arguments in a readable format."""
    config.logger.info(
        "Calling %s:\n%s",
        method,
        "\n".join(f"  {key}: {value!r}" for key, value in kwargs.items()),
    )


def _build_error_entries(sources: List[str], error_msg: str) -> List[Dict[str, Any]]:
    """Build a per-source error list from a single SDK-level error."""
    return [
        {"filename": _source_filename(source), "status": "error", "error": error_msg}
        for source in sources
    ]


def _unique_stem(stem: str, used_stems: Set[str]) -> str:
    """Return a unique filename stem for the current batch."""
    if stem not in used_stems:
        return stem
    counter = 1
    while f"{stem}_{counter}" in used_stems:
        counter += 1
    return f"{stem}_{counter}"


async def _build_result_entry(
    result: Any,
    filename: str,
    stem: str,
    out_dir: Path,
    ctx: Any,
    save_to_file: bool = True,
) -> Dict[str, Any]:
    """Convert one SDK ExtractResult into a response entry."""
    if result.state == "failed":
        if ctx and ctx.request_context:
            await ctx.warning(f"Parse failed: {filename} - {result.error}")
        return {
            "filename": filename,
            "status": "error",
            "error": result.error or "Server-side parse failed",
        }

    if result.markdown is None:
        return {
            "filename": filename,
            "status": "error",
            "error": "Parse succeeded but no Markdown was returned",
        }

    entry: Dict[str, Any] = {
        "filename": filename,
        "status": "success",
        "content": result.markdown,
    }

    if save_to_file:
        md_path = out_dir / f"{stem}.md"
        try:
            md_path.write_text(result.markdown, encoding="utf-8")
            extract_path = str(md_path)
        except Exception as exc:
            config.logger.warning("Failed to save Markdown for %s: %s", filename, exc)
            extract_path = str(out_dir)
        entry["extract_path"] = extract_path
        if ctx and ctx.request_context:
            await ctx.info(f"Saved: {filename} -> {extract_path}")

    if result.zip_url:
        entry["zip_url"] = result.zip_url

    # MINERU_DEBUG 开启时，将 task_id 附加到结果中，方便开发排查
    if config.logger.isEnabledFor(logging.DEBUG):
        task_id = getattr(result, "task_id", None)
        if task_id:
            entry["task_id"] = task_id

    return entry


async def _extract_flash(
    sources: List[str],
    lang: str,
    page_ranges_map: Optional[Dict[int, str]],
    out_dir: Path,
    ctx: Any,
    used_stems: Set[str],
    save_to_file: bool = True,
) -> List[Dict[str, Any]]:
    """Process sources one-by-one in Flash mode."""
    from mineru.client import MinerU
    from mineru.exceptions import MinerUError

    processed: List[Dict[str, Any]] = []
    for index, source in enumerate(sources):
        filename = _source_filename(source)

        page_range_raw = page_ranges_map.get(index) if page_ranges_map else None
        page_range: Optional[str] = None
        if page_range_raw:
            page_range = _sanitize_flash_page_range(page_range_raw)
            if page_range is None and ctx and ctx.request_context:
                await ctx.warning(
                    "Flash mode only supports 'N' or 'N-M' page ranges (for example '1-10'). "
                    f"Ignoring invalid range '{page_range_raw}' for {filename}."
                )

        if ctx and ctx.request_context:
            await ctx.info(f"[{index + 1}/{len(sources)}] Processing: {filename}")

        _log_sdk_call("flash_extract", source=source, language=lang, page_range=page_range)

        try:
            def _run_one() -> Any:
                with MinerU(token=None) as client:
                    return client.flash_extract(source, language=lang, page_range=page_range)

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, _run_one)
            base = Path(filename).stem
            if page_range:
                base = f"{base}_{page_range}"
            stem = _unique_stem(base, used_stems)
            used_stems.add(stem)
            entry = await _build_result_entry(result, filename, stem, out_dir, ctx, save_to_file)
        except (MinerUError, Exception) as exc:
            if ctx and ctx.request_context:
                await ctx.error(f"Failed ({filename}): {exc}")
            entry = {"filename": filename, "status": "error", "error": str(exc)}

        processed.append(entry)

    return processed


async def _extract_batch(
    sources: List[str],
    enable_ocr: Optional[bool],
    lang: str,
    sdk_model: Optional[str],
    page_ranges_map: Optional[Dict[int, str]],
    out_dir: Path,
    ctx: Any,
    token: str,
    used_stems: Set[str],
    save_to_file: bool = True,
) -> List[Dict[str, Any]]:
    """Process sources as a batch via the MinerU API."""
    from mineru.client import FileParam, MinerU
    from mineru.exceptions import MinerUError

    file_params = (
        {
            sources[index]: FileParam(pages=page_range)
            for index, page_range in page_ranges_map.items()
            if index < len(sources)
        }
        if page_ranges_map
        else None
    )

    _log_sdk_call(
        "extract_batch",
        sources=sources,
        model=sdk_model,
        ocr=enable_ocr,
        language=lang,
        file_params=file_params,
    )

    try:
        def _run_batch() -> List[Any]:
            with MinerU(token=token) as client:
                kwargs: Dict[str, Any] = dict(model=sdk_model, language=lang, file_params=file_params)
                if enable_ocr is not None:
                    kwargs["ocr"] = enable_ocr
                return list(client.extract_batch(sources, **kwargs))

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _run_batch)
    except (MinerUError, Exception) as exc:
        if ctx and ctx.request_context:
            await ctx.error(f"SDK error: {exc}")
        return _build_error_entries(sources, str(exc))

    processed: List[Dict[str, Any]] = []
    for index, result in enumerate(results):
        source = sources[index] if index < len(sources) else ""
        filename = result.filename or _source_filename(source)
        page_range = page_ranges_map.get(index) if page_ranges_map else None
        base = Path(filename).stem
        if page_range:
            base = f"{base}_{page_range}"
        stem = _unique_stem(base, used_stems)
        used_stems.add(stem)
        entry = await _build_result_entry(result, filename, stem, out_dir, ctx, save_to_file)
        processed.append(entry)

    return processed


async def extract_sources(
    sources: List[str],
    enable_ocr: Optional[bool] = None,
    language: str = "ch",
    model: Optional[str] = None,
    page_ranges_map: Optional[Dict[int, str]] = None,
    output_dir: str = config.DEFAULT_OUTPUT_DIR,
    ctx: Any = None,
    token: Optional[str] = None,
    save_to_file: bool = True,
) -> List[Dict[str, Any]]:
    """Extract a mixed list of local file paths and/or URLs to Markdown via the MinerU SDK."""
    if not sources:
        return []

    token = token or config.MINERU_API_TOKEN
    use_flash = not token
    lang = language or "ch"
    out_dir = Path(output_dir)
    if save_to_file:
        out_dir.mkdir(parents=True, exist_ok=True)

    if ctx and ctx.request_context:
        if use_flash:
            await ctx.info(
                f"Flash mode: {len(sources)} file(s), markdown only, 20 pages / 10 MB limit."
            )
        else:
            await ctx.info(f"Processing {len(sources)} file(s) with full capability. Max 600 pages or 200 MB per file.")

    used_stems: Set[str] = {p.stem for p in out_dir.glob("*.md")} if save_to_file and out_dir.exists() else set()

    if use_flash:
        return await _extract_flash(
            sources,
            lang,
            page_ranges_map,
            out_dir,
            ctx,
            used_stems,
            save_to_file,
        )
    return await _extract_batch(
        sources,
        enable_ocr,
        lang,
        model,
        page_ranges_map,
        out_dir,
        ctx,
        token,
        used_stems,
        save_to_file,
    )


def _source_filename(source: str) -> str:
    """Derive a display filename from a path or URL."""
    if source.startswith(("http://", "https://")):
        name = source.split("?")[0].split("/")[-1]
        return name or source
    return Path(source).name
