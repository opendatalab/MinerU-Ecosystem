"""Startup banner for MinerU MCP server — printed to stderr on launch."""

import sys

# The icon is a faithful ASCII rendering of the MinerU SVG logo emblem:
#   • Two outer arcs form a rounded "book-spine" / shield shape
#   • An inner raised panel sits inside, creating the layered look
#   • Two dots at the top represent the two circular accent marks in the SVG
#   • The right column shows the "MinerU MCP" wordmark
_BANNER = r"""
  ┌─────────────────────────────────────────────────────────┐
  │  __  __ _                  _   _   __  __  ____  ____   │
  │ |  \/  (_)_ __   ___ _ __ | | | | |  \/  |/ ___||  _ \  │
  │ | |\/| | | '_ \ / _ \ '__|| | | | | |\/| | |    | |_) | │
  │ | |  | | | | | |  __/ |   | |_| | | |  | | |___ |  __/  │
  │ |_|  |_|_|_| |_|\___|_|    \___/  |_|  |_|\____||_|     │
  └─────────────────────────────────────────────────────────┘
"""

_INFO_TEMPLATE = """\
  Transport : {transport}
  Host      : {host}
  Output dir: {output_dir}

  Tools available:
    • parse_documents   — Convert PDF / Word / PPT / images → Markdown
    • get_ocr_languages — List supported OCR languages

  Powered by MinerU  ·  https://mineru.net/
{extra}"""


def print_banner(
    transport: str = "stdio",
    host: str = "",
    output_dir: str = "",
) -> None:
    """Print the MinerU MCP startup banner to stderr.

    Always writes to stderr so it never corrupts the stdio MCP wire.
    """
    if transport in ("streamable-http", "sse"):
        display_host = host or "0.0.0.0"
    else:
        display_host = "— (stdio, no network port)"

    if not output_dir:
        output_dir = "~/mineru-downloads (default)"

    extra = ""

    info = _INFO_TEMPLATE.format(
        transport=transport,
        host=display_host,
        output_dir=output_dir,
        extra=extra,
    )

    print(_BANNER, file=sys.stderr)
    print(info, file=sys.stderr)
