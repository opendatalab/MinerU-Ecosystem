"""MinerU File转Markdown转换的FastMCP服务器实现。"""

import traceback

import uvicorn
from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from . import config
from .tools.tools import register_tools

# Tracks the port when running in HTTP mode (kept for potential future use)
_server_host: str = "127.0.0.1"
_server_port: int = 8001


_HEADER = """\
┌─────────────────────────────────────────┐
 MinerU MCP Server
└─────────────────────────────────────────┘
  PDF · Word · PPT · images  →  Markdown
  https://mineru.net/
"""

_INSTRUCTIONS = _HEADER + """
You are connected to MinerU, a document-to-Markdown conversion service.
你已连接到 MinerU，这是一个文档转 Markdown 的转换服务。

## When to call parse_documents / 何时调用 parse_documents

Call parse_documents IMMEDIATELY — without asking for confirmation — whenever:
以下情况请立即调用 parse_documents，无需向用户确认：

- The user provides any local file path (e.g. /Users/…, ~/…, C:\\…)
  用户提供了本地文件路径（如 /Users/…、~/…、C:\\…）
- The user provides any URL pointing to a document or image
  用户提供了指向文档或图片的 URL
- The user says "parse", "convert", "read", "extract text from", or "summarize" a file
  用户说"解析"、"转换"、"读取"、"提取文本"或"ocr"某个文件
- The user attaches or mentions a PDF, Word (.doc/.docx), PPT (.ppt/.pptx), image (jpg/jpeg/png),
  or spreadsheet (xls/xlsx)
  用户提及或附上了 PDF、Word、PPT、图片或表格文件

## How to call it / 调用方式

- Pass ALL file paths/URLs together in `file_sources` (mixed lists supported)
  将所有路径/URL 一并放入 `file_sources`（支持路径与 URL 混合）
- Set `language` to the document language name in English, e.g. "Chinese", "English", "Japanese"
  将 `language` 设置为文档语言的英文名称，如 "Chinese"、"English"、"Japanese"
- Use `enable_ocr=True` for scanned PDFs or images containing text
  扫描版 PDF 或含文字的图片请设置 `enable_ocr=True`
- Set `output_dir` if the user specifies a save location
  如用户指定保存位置，请设置 `output_dir`

## Flash mode (no API token) / Flash 模式（无 Token）

When no MINERU_TOKEN is set, Flash mode is used automatically — free, no sign-up, markdown only.
Limits: 20 pages / 10 MB per file. Supported: PDF, images (png/jpg/jpeg/jp2/webp/gif/bmp), Docx, PPTx, xls, xlsx.
未配置 MINERU_TOKEN 时自动使用 Flash 模式，免费无需注册，仅输出 Markdown。
限制：单文件最大 20 页 / 10 MB。支持：PDF、图片、Docx、PPTx、xls、xlsx。

## After calling parse_documents / 调用后

ALWAYS include the `message` field from the tool response verbatim in your reply to the user.
Do NOT skip or paraphrase it. It is a required part of every successful parse response.
调用成功后，必须将工具响应中的 `message` 字段原文包含在回复中，不得省略或改写。

## Available tools / 可用工具

- parse_documents   — Parse local files or URLs into Markdown / 将本地文件或 URL 解析为 Markdown
- get_ocr_languages — List supported OCR languages / 列出支持的 OCR 语言
"""
_INSTRUCTIONS += (
    "- clean_logs        — Delete old server log files / 删除旧的服务器日志文件\n"
    if config.ENABLE_LOG else ""
)

# 初始化 FastMCP 服务器
mcp = FastMCP(
    name="MinerU File to Markdown Conversion",
    instructions=_INSTRUCTIONS,
    **({} if config.MINERU_TOKEN else {"auth": None}),
)

# Markdown 文件的输出目录
output_dir = config.DEFAULT_OUTPUT_DIR


def get_output_dir() -> str:
    """返回当前输出目录路径。"""
    return output_dir


def set_output_dir(dir_path: str) -> str:
    """设置转换后文件的输出目录。"""
    global output_dir
    output_dir = dir_path
    config.ensure_output_dir(output_dir)
    return output_dir


def cleanup_resources() -> None:
    """清理全局资源。"""
    config.logger.info("资源清理完成")


def create_starlette_app(mcp_server, *, debug: bool = False) -> Starlette:
    """创建用于SSE传输的Starlette应用。

    Args:
        mcp_server: MCP服务器实例
        debug: 是否启用调试模式

    Returns:
        Starlette: 配置好的Starlette应用实例
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        """处理SSE连接请求。"""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


def run_server(mode=None, port=8001, host="0.0.0.0") -> None:
    """运行 FastMCP 服务器。

    Args:
        mode: 运行模式，支持stdio、sse、streamable-http
        port: 服务器端口，默认为8001，仅在HTTP模式下有效
        host: 服务器主机地址，默认为127.0.0.1，仅在HTTP模式下有效
    """
    global _server_host, _server_port

    config.ensure_output_dir(output_dir)
    if config.ENABLE_LOG:
        config.start_file_logging()
    config.logger.info("MinerU MCP Server starting (transport=%s, port=%s)", mode or "stdio", port)

    if not config.MINERU_TOKEN:
        config.logger.info(
            "未设置 API Token，将使用 Flash 模式（免费，无需认证，限 20 页 / 10 MB）。"
            " 如需完整功能，请设置 MINERU_TOKEN 或 MINERU_API_TOKEN 环境变量。"
        )

    mcp_server = mcp._mcp_server

    try:
        if mode == "sse":
            config.logger.info(f"启动SSE服务器: {host}:{port}")
            starlette_app = create_starlette_app(mcp_server, debug=True)
            uvicorn.run(starlette_app, host=host, port=port)
        elif mode == "streamable-http":
            _server_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
            _server_port = port
            config.logger.info(f"启动Streamable HTTP服务器: {host}:{port}")
            http_app = mcp.http_app()
            uvicorn.run(http_app, host=host, port=port)
        else:
            config.logger.info("启动STDIO服务器")
            mcp.run(mode or "stdio")
    except Exception as e:
        config.logger.error(f"\n❌ 服务异常退出: {str(e)}")
        traceback.print_exc()
    finally:
        cleanup_resources()


# Register tools with the MCP instance, injecting dependencies
register_tools(mcp, get_output_dir)
