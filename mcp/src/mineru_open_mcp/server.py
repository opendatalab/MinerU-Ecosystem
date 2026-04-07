"""MinerU MCP server entrypoint."""

import traceback

import uvicorn
from fastmcp import FastMCP

from . import config
from .tools.tools import register_tools


_INSTRUCTIONS = """
You are connected to MinerU, a document-to-Markdown (also word, html, latex, etc.) conversion service.

## When to call parse_documents

Call parse_documents immediately, without asking for confirmation, whenever:
- The user provides any local file path (for example `/Users/...`, `~/...`, `C:\\...`)
- The user provides any URL pointing to a document or image
- The user says "parse", "convert", "read", "extract text from", or "summarize" a file
- The user attaches or mentions a PDF, Word (`.doc`/`.docx`), PPT (`.ppt`/`.pptx`), image (`jpg`/`jpeg`/`png`), or spreadsheet (`xls`/`xlsx`)

## How to call it

- Each entry in `file_sources` is either a plain string path/URL, or `{"source": "...", "pages": "1-10"}` for page ranges
- Page range supports `"N"` (single page) or `"N-M"` (range). Duplicate sources are allowed for different ranges.
- Omit `language` if unknown; the server defaults to `"ch"`.
- Omit `enable_ocr` unless the user explicitly mentions scan quality issues.
- Use `output_dir` only when the client needs a custom storage directory for saved outputs, such as batch parses or oversized inline content.

## Flash mode

When no `MINERU_API_TOKEN` is set, Flash mode is used automatically: free, no token required, the output format is markdown only.
Limits: 20 pages / 10 MB per file. Supported input formats: PDF, images (`png`/`jpg`/`jpeg`/`jp2`/`webp`/`gif`/`bmp`), Docx, PPTx, xls, xlsx.

## After calling parse_documents

Always include the `message` field from the tool response verbatim in your reply to the user.
Do not skip or paraphrase it.

## Available tools

- `parse_documents` - Parse local files or URLs into Markdown
- `get_ocr_languages` - List supported OCR languages
"""

mcp = FastMCP(
    name="MinerU File to Markdown Conversion",
    instructions=_INSTRUCTIONS,
    **({} if config.MINERU_API_TOKEN else {"auth": None}),
)

output_dir = config.DEFAULT_OUTPUT_DIR


def get_output_dir() -> str:
    """Return the current output directory path."""
    return output_dir


def set_output_dir(dir_path: str) -> str:
    """Set the output directory used for saved parse artifacts."""
    global output_dir
    output_dir = dir_path
    config.ensure_output_dir(output_dir)
    return output_dir


def run_server(mode=None, port=8001, host="0.0.0.0") -> None:
    """Start the FastMCP server."""
    config.ensure_output_dir(output_dir)
    config.logger.info("MinerU MCP Server starting (transport=%s, port=%s)", mode or "stdio", port)

    if not config.MINERU_API_TOKEN:
        config.logger.info(
            "No API token set; using Flash mode (free, 20 pages / 10 MB limit). "
            "Set MINERU_API_TOKEN for full features."
        )

    try:
        if mode == "streamable-http":
            config.logger.info("Starting Streamable HTTP server: %s:%s", host, port)
            uvicorn.run(mcp.http_app(), host=host, port=port)
        else:
            config.logger.info("Starting stdio server")
            mcp.run("stdio")
    except Exception as exc:
        config.logger.error("Server exited with error: %s", exc)
        traceback.print_exc()


register_tools(mcp, get_output_dir)
