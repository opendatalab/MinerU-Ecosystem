"""MCP tool registration for MinerU document parsing."""

import contextlib
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

from fastmcp import Context, FastMCP
from pydantic import Field

from .. import config
from .extract import extract_sources

_ALL_LANGUAGES: List[str] = [
    "ch (Chinese, English, Chinese Traditional)",
    "ch_server (Chinese, English, Chinese Traditional, Japanese)",
    "en (English)",
    "korean (Korean, English)",
    "japan (Chinese, English, Chinese Traditional, Japanese)",
    "chinese_cht (Chinese, English, Chinese Traditional, Japanese)",
    "ta (Tamil, English)",
    "te (Telugu, English)",
    "ka (Kannada)",
    "el (Greek, English)",
    "th (Thai, English)",
    (
        "latin (French, German, Afrikaans, Italian, Spanish, Bosnian, Portuguese, Czech, Welsh, "
        "Danish, Estonian, Irish, Croatian, Uzbek, Hungarian, Serbian (Latin), Indonesian, "
        "Occitan, Icelandic, Lithuanian, Maori, Malay, Dutch, Norwegian, Polish, Slovak, "
        "Slovenian, Albanian, Swedish, Swahili, Tagalog, Turkish, Latin, Azerbaijani, Kurdish, "
        "Latvian, Maltese, Pali, Romanian, Vietnamese, Finnish, Basque, Galician, Luxembourgish, "
        "Romansh, Catalan, Quechua)"
    ),
    "arabic (Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi, English)",
    "east_slavic (Russian, Belarusian, Ukrainian, English)",
    (
        "cyrillic (Russian, Belarusian, Ukrainian, Serbian (Cyrillic), Bulgarian, Mongolian, "
        "Abkhazian, Adyghe, Kabardian, Avar, Dargin, Ingush, Chechen, Lak, Lezgin, Tabasaran, "
        "Kazakh, Kyrgyz, Tajik, Macedonian, Tatar, Chuvash, Bashkir, Malian, Moldovan, Udmurt, "
        "Komi, Ossetian, Buryat, Kalmyk, Tuvan, Sakha, Karakalpak, English)"
    ),
    (
        "devanagari (Hindi, Marathi, Nepali, Bihari, Maithili, Angika, Bhojpuri, Magahi, "
        "Santali, Newari, Konkani, Sanskrit, Haryanvi, English)"
    ),
]

_CONTENT_MAX_PER_FILE = 20_000
_CONTENT_MAX_TOTAL = 60_000


def _brand_message(saved_paths: Optional[List[tuple[str, str]]] = None) -> str:
    """Build the user-facing completion message."""
    
    if not saved_paths:
        return f"Parsing complete!\n"
    if len(saved_paths) == 1:
        _, path = saved_paths[0]
        return f"Parsing complete!\nSaved to: {path}\n"
    lines = ["Parsing complete!", "Files saved to:"]
    for i, (filename, path) in enumerate(saved_paths, 1):
        lines.append(f"  [{i}] {filename} → {path}")

    return "\n".join(lines)


def _save_full_markdown(entry: Dict[str, Any], content: str, out_dir: Path) -> None:
    """Persist full markdown for truncated inline responses."""
    try:
        filename = entry.get("filename", "output")
        stem = Path(filename).stem or "output"
        stem_dir = out_dir / stem
        stem_dir.mkdir(parents=True, exist_ok=True)
        md_path = stem_dir / f"{stem}.md"
        md_path.write_text(content, encoding="utf-8")
        entry["extract_path"] = str(stem_dir)
    except Exception as exc:
        config.logger.warning(
            "Failed to save truncated Markdown for %s: %s",
            entry.get("filename", "?"),
            exc,
        )


def _apply_content_limits(results: List[Dict[str, Any]], output_dir: str = "") -> List[Dict[str, Any]]:
    """Trim oversized inline content and save the full markdown to disk."""
    success_with_content = sum(
        1 for result in results if result.get("status") == "success" and "content" in result
    )
    per_file_cap = min(_CONTENT_MAX_PER_FILE, _CONTENT_MAX_TOTAL // max(success_with_content, 1))
    out_dir = Path(output_dir) if output_dir else None
    normalized: List[Dict[str, Any]] = []
    for result in results:
        if result.get("status") == "success" and "content" in result:
            result = result.copy()
            full_content = result["content"]
            result["content_chars"] = len(full_content)
            if len(full_content) > per_file_cap:
                if out_dir and "extract_path" not in result:
                    _save_full_markdown(result, full_content, out_dir)
                result["content"] = full_content[:per_file_cap]
                result["truncated"] = True
            else:
                result["truncated"] = False
        normalized.append(result)
    return normalized


def _format_results(
    results: List[Dict[str, Any]],
    output_dir: str = "",
    include_content: bool = True,
) -> Dict[str, Any]:
    """Collapse raw result entries into the standard tool response shape."""
    if include_content:
        results = _apply_content_limits(results, output_dir=output_dir)
    else:
        results = [{k: v for k, v in r.items() if k != "content"} for r in results]

    # Strip zip_url — not exposed to the user
    results = [{k: v for k, v in r.items() if k != "zip_url"} for r in results]

    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count
    saved_paths = [
        (r.get("filename", ""), r["extract_path"])
        for r in results
        if r.get("status") == "success" and r.get("extract_path")
    ]

    response: Dict[str, Any] = {
        "status": "error" if success_count == 0 else "partial_success" if error_count > 0 else "success",
        "results": results,
        "summary": {
            "total_files": len(results),
            "success_count": success_count,
            "error_count": error_count,
        },
    }
    if success_count > 0:
        response["message"] = _brand_message(saved_paths=saved_paths or None)
    return response


async def _validate_sources(
    sources: List[str],
    ctx: Context,
) -> tuple[List[str], List[Dict[str, Any]]]:
    """Split sources into valid entries and pre-validation errors."""
    valid_sources: List[str] = []
    pre_errors: List[Dict[str, Any]] = []
    for source in sources:
        if source.startswith(("http://", "https://")):
            valid_sources.append(source)
        elif not Path(source).exists():
            if ctx and ctx.request_context:
                await ctx.warning(f"File not found, skipping: {source}")
            pre_errors.append(
                {
                    "filename": Path(source).name,
                    "status": "error",
                    "error": f"File not found: {source}",
                }
            )
        else:
            valid_sources.append(source)
    return valid_sources, pre_errors


async def _parse(
    file_sources: List[str],
    enable_ocr: Optional[bool],
    language: str,
    page_ranges_map: Optional[Dict[int, str]],
    output_dir: str,
    ctx: Context,
    token: Optional[str] = None,
    model: Optional[str] = None,
    save_to_file: bool = False,
) -> Dict[str, Any]:
    """Parse files using the MinerU SDK."""
    if not file_sources:
        return _format_results([], output_dir=output_dir)

    valid_sources, pre_errors = await _validate_sources(file_sources, ctx)

    remapped: Optional[Dict[int, str]] = None
    if page_ranges_map and valid_sources:
        valid_index = 0
        remap: Dict[int, str] = {}
        for file_index, source in enumerate(file_sources):
            if valid_index < len(valid_sources) and valid_sources[valid_index] == source:
                if file_index in page_ranges_map:
                    remap[valid_index] = page_ranges_map[file_index]
                valid_index += 1
        remapped = remap or None

    all_results: List[Dict[str, Any]] = list(pre_errors)
    if valid_sources:
        sdk_results = await extract_sources(
            sources=valid_sources,
            enable_ocr=enable_ocr,
            language=language,
            model=model,
            page_ranges_map=remapped,
            output_dir=output_dir,
            ctx=ctx,
            token=token,
            save_to_file=save_to_file,
        )
        all_results.extend(sdk_results)

    return _format_results(all_results, output_dir=output_dir, include_content=not save_to_file)


_FILE_SOURCES_FIELD = Field(
    description=(
        "Files to parse. Each entry is either:\n"
        "  - a plain string: a local file path or URL\n"
        "  - a dict {\"source\": \"...\", \"pages\": \"N-M\"}: with an optional page range\n"
        "Page range: \"N\" (single page) or \"N-M\" (for example \"1-10\"). PDF only. "
        "Duplicate sources are allowed, for example the same PDF with different ranges.\n"
        "Examples:\n"
        "  [\"report.pdf\"]\n"
        "  [{\"source\": \"report.pdf\", \"pages\": \"1-5\"}]\n"
        "  [{\"source\": \"a.pdf\", \"pages\": \"1-3\"}, {\"source\": \"a.pdf\", \"pages\": \"10-15\"}]\n"
        "  [\"https://example.com/doc.pdf\", \"local.docx\"]"
    )
)

_ENABLE_OCR_FIELD = Field(
    description=(
        "OCR mode:\n"
        "  null (default) - auto-detect: the server decides whether OCR is needed.\n"
        "  true           - force OCR on when the user mentions poor scan quality.\n"
        "  false          - disable OCR.\n"
        "Omit this parameter unless the user explicitly mentions scan quality issues."
    )
)

_LANGUAGE_FIELD = Field(
    description=(
        "OCR language code. Omit if unknown; the server defaults to \"ch\" (Chinese + English). "
        "Infer from the document filename when possible, for example \"manual_en.pdf\" -> \"en\". "
        "Common codes: \"ch\", \"en\", \"japan\", \"korean\", \"latin\", "
        "\"arabic\", \"cyrillic\", \"devanagari\". Full list: call get_ocr_languages."
    )
)

_OUTPUT_DIR_FIELD = Field(
    description=(
        "Directory used when parsed results need to be saved locally, such as batch parsing "
        "or oversized inline content. Defaults to the server-configured directory."
    )
)

_MODEL_FIELD = Field(
    description=(
        "Parsing model. Set to \"html\" only when all file_sources are web page URLs. "
        "Otherwise omit it and let MinerU auto-select the appropriate model. Ignored in Flash mode."
    )
)


def _extract_request_token() -> Optional[str]:
    """Extract the MinerU API token from the current HTTP request."""
    with contextlib.suppress(Exception):
        from fastmcp.server.dependencies import get_http_request

        request = get_http_request()
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip() or None
    return None


def _normalize_file_sources(
    file_sources: List[Union[str, Dict[str, str]]],
) -> tuple[List[str], Optional[Dict[int, str]]]:
    """Parse mixed file_sources entries into sources plus optional page ranges."""
    sources: List[str] = []
    page_ranges_map: Dict[int, str] = {}
    for entry in file_sources:
        if isinstance(entry, str):
            sources.append(entry)
        elif isinstance(entry, dict):
            source = entry.get("source", "")
            pages = entry.get("pages") or None
            sources.append(source)
            if pages:
                page_ranges_map[len(sources) - 1] = pages
        else:
            sources.append(str(entry))
    return sources, page_ranges_map or None


def register_tools(mcp: FastMCP, get_output_dir) -> None:
    """Register all MCP tools onto the given FastMCP instance."""

    @mcp.tool(
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def parse_documents(
        file_sources: Annotated[List[Union[str, Dict[str, str]]], _FILE_SOURCES_FIELD],
        enable_ocr: Annotated[Optional[bool], _ENABLE_OCR_FIELD] = None,
        language: Annotated[Optional[str], _LANGUAGE_FIELD] = None,
        model: Annotated[Optional[str], _MODEL_FIELD] = None,
        output_dir: Annotated[Optional[str], _OUTPUT_DIR_FIELD] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Parse local files or URLs into Markdown."""
        sources, page_ranges_map = _normalize_file_sources(file_sources)
        resolved_output_dir = output_dir or get_output_dir()
        return await _parse(
            sources,
            enable_ocr,
            language or "ch",
            page_ranges_map,
            resolved_output_dir,
            ctx,
            token=_extract_request_token(),
            model=model,
            save_to_file=len(sources) > 1,
        )

    @mcp.tool(
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def get_ocr_languages() -> Dict[str, Any]:
        """List all OCR languages supported by MinerU."""
        try:
            return {"status": "success", "languages": _ALL_LANGUAGES}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
