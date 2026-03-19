"""MCP tool registration for MinerU document parsing."""

import contextlib
from typing import Annotated, Any, Dict, List, Optional

from fastmcp import Context, FastMCP
from pydantic import Field

from .. import config
from ..language import get_language_list
from .handlers import parse_remote

_FILE_SOURCES_REMOTE_FIELD = Field(
    description=(
        "File paths or URLs to parse. Pass any local path (e.g. /Users/foo/doc.pdf) "
        "or a remote URL pointing to a PDF, Word doc, PPT, or image. "
        "Mixed lists of paths and URLs are supported.\n"
        "要解析的文件路径或 URL 列表，支持本地路径与远程 URL 混合传入，"
        "格式涵盖 PDF、Word、PPT 及图片（jpg/jpeg/png）。"
    )
)


def _extract_request_token() -> Optional[str]:
    """Extract the MinerU API token from the current HTTP request.

    Checks (in order):
    1. ``?api_key=`` query parameter
    2. ``Authorization: Bearer <token>`` header

    Returns None when not running under HTTP transport (e.g. stdio mode).
    """
    with contextlib.suppress(Exception):
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        # 1. Query param ?api_key=
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        # 2. Authorization: Bearer <token>
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip() or None
    return None


_ENABLE_OCR_FIELD = Field(
    description=(
        "Enable OCR for scanned PDFs or images containing text. Default False. "
        "/ 对扫描版PDF或含文字图片启用OCR识别，默认 False。"
    )
)

_LANGUAGE_FIELD = Field(
    description=(
        'Language of the document. The model does NOT auto-detect language — '
        'always infer this from the document content or the user\'s request and pass it. '
        'Pass the full language name in English: "Chinese", "English", "Japanese", '
        '"Korean", "French", "Arabic", "Tamil", "Macedonian". '
        'The server maps the name to the correct SDK code automatically. '
        'Default is "Chinese". '
        '/ 文档语言。模型不会自动检测语言，必须传入此参数。'
        '请根据文档内容或用户请求推断语言并传入。'
        '使用英文语言名称，如 "Chinese"、"English"、"Japanese"、"Korean"、'
        '"French"、"Arabic"、"Tamil"、"Macedonian"。服务端会自动映射到 SDK 代码。'
        '默认为 "Chinese"。'
    )
)

_OUTPUT_DIR_FIELD = Field(
    description=(
        "Directory path to save output files. Defaults to the server-configured directory. "
        "/ 输出文件保存目录，默认使用服务器配置的目录。"
    )
)

_MODEL_FIELD = Field(
    description=(
        'Parsing model. Rules for setting this: '
        '(1) If ALL file_sources are web page URLs (http/https pointing to HTML pages), '
        'set model="html". '
        '(2) If file_sources are documents or images, or a mix of documents and URLs, '
        'leave this blank — MinerU auto-selects "vlm" for documents and "html" for web pages. '
        '(e.g. Tamil, Telugu, Greek, Thai, Arabic, Cyrillic-script, Devanagari). '
        'Ignored in Flash mode. '
        '/ 解析模型。使用规则：'
        '(1) 若 file_sources 全部为网页 URL（http/https HTML 页面），设置 model="html"。'
        '(2) 若为文档/图片，或文档与 URL 混合，留空——MinerU 自动选择（文档用 "vlm"，网页用 "html"）。'
        'Flash 模式下忽略此参数。'
    )
)

_EXTRA_FORMATS_FIELD = Field(
    description=(
        'Additional output formats to generate alongside Markdown. '
        'Accepted values: "docx" (Word), "html", "latex", "all" (all three). '
        'Ask the user if they need Word, HTML, or LaTeX output in addition to Markdown, '
        'then pass the requested formats here. '
        'Not available in Flash mode (no API token — Flash outputs markdown only). '
        '/ 除 Markdown 外的额外输出格式。可选值："docx"（Word）、"html"、"latex"、"all"（全部三种）。'
        '如用户需要 Word、HTML 或 LaTeX 格式，请传入此参数。'
        '注意：Flash 模式（无 Token）不支持此参数，仅输出 Markdown。'
    )
)


def register_tools(mcp: FastMCP, get_output_dir) -> None:
    """Register all MCP tools onto the given FastMCP instance."""

    _parse_docs_doc = (
        "Parse files or URLs into Markdown (cloud API mode).\n"
        "将文件或 URL 解析为 Markdown（云端 API 模式）。\n\n"
        "Call this tool immediately whenever the user provides a file path or URL — no confirmation needed.\n"
        "当用户提供文件路径或 URL 时，立即调用此工具，无需向用户确认。\n\n"
        "Supported formats / 支持格式: PDF, .doc, .docx, .ppt, .pptx, jpg, jpeg, png.\n\n"
        "API token (MINERU_API_TOKEN) is OPTIONAL. When no token is configured, the server\n"
        "automatically uses Flash mode — free, no sign-up required, markdown output only,\n"
        "limited to 20 pages / 10 MB per file (PDF/images/Docx/PPTx/xls/xlsx). "
        "With a token, full API features are available\n"
        "(extra formats, OCR, higher limits). Do NOT ask the user to provide a token;\n"
        "just call the tool and it will work in Flash mode if no token is set.\n"
        "API Token（MINERU_API_TOKEN）为可选项。未配置时自动使用 Flash 模式（免费，无需注册，\n"
        "仅输出 Markdown，单文件限 20 页 / 10 MB，支持 PDF/图片/Docx/PPTx/xls/xlsx）。"
        "配置 Token 后可使用完整功能。\n"
        "请勿要求用户提供 Token，直接调用即可。\n\n"
        "After a successful call, ALWAYS include the `message` field verbatim in your reply.\n"
        "调用成功后，必须将响应中的 `message` 字段原文写入回复，不得省略或改写。\n\n"
        "Returns / 返回:\n"
        '    success / 成功: {"status": "success", "results": [...], "summary": {...}, "message": "..."}  — content field is a 20-char preview; full Markdown is saved to extract_path on disk.\n'
        '    error   / 失败: {"status": "error",   "results": [...], "summary": {...}}'
    )

    @mcp.tool()
    async def parse_documents(
        file_sources: Annotated[List[str], _FILE_SOURCES_REMOTE_FIELD],
        enable_ocr: Annotated[bool, _ENABLE_OCR_FIELD] = False,
        language: Annotated[str, _LANGUAGE_FIELD] = "Chinese",
        model: Annotated[Optional[str], _MODEL_FIELD] = None,
        page_ranges: Annotated[
            Optional[List[str]],
            Field(description=(
                'Per-file page ranges as an array aligned with file_sources. '
                'e.g. ["1-3", null, "5,7-9"] parses pages 1-3 of the first file, '
                'all pages of the second, and pages 5,7-9 of the third. '
                'Use null or "" to include all pages for a file. '
                'Range syntax: "2,4-6" for pages 2,4,5,6 or "2--2" for page 2 to second-last.\n'
                '按 file_sources 顺序对应的页码范围数组，如 ["1-3", null, "5,7-9"]；'
                '对应位置填 null 或 "" 表示解析该文件全部页面。'
                '范围语法："2,4-6" 表示第2、4-6页，"2--2" 表示第2页至倒数第2页。'
            )),
        ] = None,
        extra_formats: Annotated[Optional[List[str]], _EXTRA_FORMATS_FIELD] = None,
        output_dir: Annotated[Optional[str], _OUTPUT_DIR_FIELD] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        return await parse_remote(
            file_sources, enable_ocr, language, page_ranges,
            output_dir or get_output_dir(), ctx,
            token=_extract_request_token(),
            extra_formats=extra_formats,
            model=model,
        )

    parse_documents.__doc__ = _parse_docs_doc

    @mcp.tool()
    async def get_ocr_languages() -> Dict[str, Any]:
        """List all OCR languages supported by MinerU.
        列出 MinerU 支持的所有 OCR 语言。

        Call this when the user asks which languages are available for OCR.
        当用户询问 OCR 支持哪些语言时调用此工具。

        Returns / 返回:
            success / 成功: {"status": "success", "languages": [...]}
            error   / 失败: {"status": "error",   "error":   "<message>"}
        """
        try:
            return {"status": "success", "languages": get_language_list()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    if config.ENABLE_LOG:
        @mcp.tool()
        async def clean_logs() -> Dict[str, Any]:
            """Delete old MinerU MCP log files, keeping only the current session's log.
            删除旧的 MinerU MCP 日志文件，仅保留当前会话的日志。

            Call this when the user asks to clean up or delete old log files.
            当用户要求清理或删除旧日志文件时调用此工具。

            Returns / 返回:
                success / 成功: {"status": "success", "deleted": <count>, "bytes_freed": <bytes>}
                error   / 失败: {"status": "error",   "error":   "<message>"}
            """
            try:
                log_dir = config.LOG_DIR
                current = config.CURRENT_LOG_FILE

                if not log_dir.exists():
                    return {"status": "success", "deleted": 0, "bytes_freed": 0}

                deleted = 0
                bytes_freed = 0
                for log_file in log_dir.glob("*.txt"):
                    if current and log_file.resolve() == current.resolve():
                        continue
                    size = log_file.stat().st_size
                    log_file.unlink()
                    deleted += 1
                    bytes_freed += size

                return {"status": "success", "deleted": deleted, "bytes_freed": bytes_freed}
            except Exception as e:
                return {"status": "error", "error": str(e)}
