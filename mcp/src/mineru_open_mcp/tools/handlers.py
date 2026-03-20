"""Parse handler implementations and result formatting for MinerU MCP tools."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import Context

from .. import config
from .converters import convert_sources


_BRAND_MESSAGE = (
    "✅ Parsing complete!\n"
    "📁 FILES SAVED TO: {output_dir}\n"
    "Visit https://mineru.net/ for more details."
)
_ZIP_URL_HEADER = "Download links for the full results (with images):"


def _brand_message(
    output_dir: str,
    zip_entries: "Optional[List[tuple]]" = None,
) -> str:
    """Build the brand message, appending a numbered download list when zip_urls are present."""
    abs_dir = str(Path(output_dir).resolve())
    msg = _BRAND_MESSAGE.format(output_dir=abs_dir)

    if zip_entries:
        lines = [_ZIP_URL_HEADER]
        for i, (filename, url) in enumerate(zip_entries, 1):
            lines.append(f"  {i}. {filename}: {url}")
        msg += "\n" + "\n".join(lines)
    return msg


_CONTENT_PREVIEW_LEN = 20


def _truncate_content(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of result with content truncated to _CONTENT_PREVIEW_LEN characters."""
    if "content" in result and result["content"]:
        result = result.copy()
        result["content"] = result["content"][:_CONTENT_PREVIEW_LEN]
    return result


def format_results(
    results: List[Dict[str, Any]],
    output_dir: str = "",
) -> Dict[str, Any]:
    """Collapse a result list into the standard tool response shape.

    Always returns::

        {
            "status": "success" | "partial_success" | "error",
            "results": [
                {
                    "filename": str,
                    "status": "success" | "error",
                    # success fields (omitted on error):
                    "content": str,           # truncated preview
                    "extract_path": str,      # local mode only
                    "zip_url": str,           # when available
                    "saved_formats": {...},   # when extra formats saved
                    # error field (omitted on success):
                    "error": str,
                }
            ],
            "summary": {"total_files": int, "success_count": int, "error_count": int},
            "message": str,   # present only when success_count > 0
        }
    """
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count

    zip_entries: List[tuple] = [
        (r.get("filename", ""), r["zip_url"])
        for r in results
        if r.get("status") == "success" and r.get("zip_url")
    ]

    response: Dict[str, Any] = {
        "status": (
            "error" if success_count == 0
            else "partial_success" if error_count > 0
            else "success"
        ),
        "results": [_truncate_content(r) for r in results],
        "summary": {
            "total_files": len(results),
            "success_count": success_count,
            "error_count": error_count,
        },
    }
    if success_count > 0:
        response["message"] = _brand_message(output_dir, zip_entries=zip_entries)
    return response


async def _validate_sources(
    sources: List[str],
    ctx: Context,
) -> "tuple[List[str], List[Dict[str, Any]]]":
    """Split sources into valid (URL or existing file) and pre-error entries.

    Returns (valid_sources, pre_errors).
    """
    valid_sources: List[str] = []
    pre_errors: List[Dict[str, Any]] = []
    for s in sources:
        if s.startswith(("http://", "https://")):
            valid_sources.append(s)
        elif not Path(s).exists():
            await ctx.warning(f"文件不存在，跳过: {s}")
            pre_errors.append({
                "filename": Path(s).name,
                "status": "error",
                "error": f"文件不存在: {s}",
            })
        else:
            valid_sources.append(s)
    return valid_sources, pre_errors


async def parse_remote(
    file_sources: List[str],
    enable_ocr: bool,
    language: str,
    page_ranges: Optional[List[str]],
    output_dir: str,
    ctx: Context,
    token: Optional[str] = None,
    extra_formats: Optional[List[str]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse files (local paths and/or URLs) using the MinerU SDK (remote API)."""
    if not file_sources:
        return format_results([], output_dir=output_dir)

    valid_sources, pre_errors = await _validate_sources(file_sources, ctx)

    # Build page_ranges_map: keyed by valid_sources index.
    # page_ranges is an array aligned with file_sources; re-key to valid_sources indices.
    page_ranges_map: Optional[Dict[int, str]] = None
    if page_ranges and valid_sources:
        pr_by_idx = {i: r for i, r in enumerate(page_ranges) if r}

        # _validate_sources preserves order, so valid_sources is an ordered
        # subsequence of file_sources. Walk both to build the index mapping.
        fs_to_valid: Dict[int, int] = {}
        vi = 0
        for fi, s in enumerate(file_sources):
            if vi < len(valid_sources) and valid_sources[vi] == s:
                fs_to_valid[fi] = vi
                vi += 1
        page_ranges_map = {
            fs_to_valid[i]: pr
            for i, pr in pr_by_idx.items()
            if i < len(file_sources) and i in fs_to_valid
        } or None

    all_results: List[Dict[str, Any]] = list(pre_errors)

    if valid_sources:
        sdk_results = await convert_sources(
            sources=valid_sources,
            enable_ocr=enable_ocr,
            language=language,
            model=model,
            page_ranges_map=page_ranges_map,
            output_dir=output_dir,
            ctx=ctx,
            token=token,
            extra_formats=extra_formats,
        )
        config.logger.debug("sdk_results: %s", sdk_results)
        all_results.extend(sdk_results)

    success_count = sum(1 for r in all_results if r.get("status") == "success")
    await ctx.info(
        f"处理完成: 共 {len(all_results)} 个文件, "
        f"成功 {success_count}, "
        f"失败 {sum(1 for r in all_results if r.get('status') == 'error')}"
    )

    if success_count > 0:
        await ctx.info(_brand_message(output_dir))
    return format_results(all_results, output_dir=output_dir)