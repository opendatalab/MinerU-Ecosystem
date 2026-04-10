"""Command-line interface for the MinerU MCP server."""

import argparse
import sys

from . import config
from . import server

_BANNER = r"""
  +----------------------------------------------------------+
  |  __  __ _                  _   _   __  __  ____  ____   |
  | |  \/  (_)_ __   ___ _ __ | | | | |  \/  |/ ___||  _ \  |
  | | |\/| | | '_ \ / _ \ '__|| | | | | |\/| | |    | |_) | |
  | | |  | | | | | |  __/ |   | |_| | | |  | | |___ |  __/  |
  | |_|  |_|_|_| |_|\___|_|    \___/  |_|  |_|\____||_|     |
  +----------------------------------------------------------+
"""

_INFO_TEMPLATE = """\
  Transport   : {transport}
  Host        : {host}
  Output dir  : {output_dir}
  Output mode : {output_mode}

  Tools available:
    * parse_documents   - Convert PDF / Word / PPT / images -> Markdown
    * get_ocr_languages - List supported OCR languages

  Powered by MinerU  -  https://mineru.net/
"""


def _print_banner(transport: str, host: str, output_dir: str) -> None:
    """Print the startup banner to stderr without touching the MCP stdio wire."""
    display_host = host if transport == "streamable-http" else "(stdio, no network port)"
    if not output_dir:
        output_dir = "~/mineru-downloads (default)"
    output_mode = "single-file inline; batch and oversized results saved to output dir"
    print(_BANNER, file=sys.stderr)
    print(
        _INFO_TEMPLATE.format(
            transport=transport,
            host=display_host,
            output_dir=output_dir,
            output_mode=output_mode,
        ),
        file=sys.stderr,
    )


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="MinerU document-to-Markdown MCP server")

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        help="Directory used for saved batch results and oversized inline content (default: ~/mineru-downloads)",
    )
    parser.add_argument(
        "--transport",
        "-t",
        type=str,
        default="stdio",
        help="Transport mode: stdio (default), streamable-http",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8001,
        help="Server port (default: 8001, HTTP transports only)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0, HTTP transports only)",
    )

    args = parser.parse_args()

    if args.transport == "stdio" and (args.host != "0.0.0.0" or args.port != 8001):
        print("Warning: --host and --port are ignored in stdio mode.", file=sys.stderr)

    if not config.MINERU_API_TOKEN:
        print(
            "Warning: MINERU_API_TOKEN is not set; Flash mode will be used "
            "(free, 20 pages / 10 MB per file).",
            file=sys.stderr,
        )

    if args.output_dir:
        server.set_output_dir(args.output_dir)

    host_display = f"{args.host}:{args.port}" if args.transport == "streamable-http" else ""
    _print_banner(args.transport, host_display, server.get_output_dir())
    server.run_server(mode=args.transport, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
