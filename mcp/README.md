[中文文档](./README.zh-CN.md)
# MinerU Open MCP

An Official Mineru  MCP server that exposes [MinerU](https://mineru.net)'s document parsing as MCP tools. Connect any MCP-compatible AI client to convert PDFs, Word docs, PowerPoint files, spreadsheets, and images into Markdown, Word (docx), HTML, or LaTeX.

**No API key required** — Flash mode works out of the box, free with no sign-up, for files up to 20 pages / 10 MB. Set `MINERU_API_TOKEN` to unlock higher limits and extra output formats.

---

## ⚡ Quickest Way to Run — uvx (no install needed)

`mineru-open-mcp` is on PyPI. With `uv` installed, you can run it directly — no separate install step.

### Configure your MCP client

#### stdio — Claude Desktop, Cursor, Windsurf

The MCP client launches `mineru-open-mcp` as a subprocess automatically.

**Using `uvx` (recommended — always runs the latest version):**

```json
{
  "mcpServers": {
    "mineru": {
      "command": "uvx",
      "args": ["mineru-open-mcp"],
      "env": {
        "MINERU_API_TOKEN": "your_key_here"
      }
    }
  }
}
```


> **No API key?** The server runs in Flash mode — free, markdown-only, 20 pages / 10 MB per file (PDF, images, Docx, PPTx, xls, xlsx).

> **`mineru-open-mcp` not on PATH?** Use the full path: `"/Users/you/.local/bin/mineru-open-mcp"`, or use the `uvx` approach above which handles this automatically.

#### streamable-http — web-based MCP clients

Start the server manually, then point your client at it:

```bash
MINERU_API_TOKEN=your_key mineru-open-mcp --transport streamable-http --port 8001
```

```json
{
  "mcpServers": {
    "mineru": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```




## Features

- **`parse_documents`** — convert local files and/or remote URLs to Markdown; supports PDF, DOCX, PPTX, JPG, PNG, HTML; optional extra output formats (Word, HTML, LaTeX). Flash Mode also supports xls and xlsx.
- **`get_ocr_languages`** — list all OCR languages supported by MinerU
- **`clean_logs`** — delete old server log files (only available when `ENABLE_LOG=true`)
- **Flash mode** — works without an API key (free, markdown-only, 20 pages / 10 MB per file, supports PDF/images/Docx/PPTx/xls/xlsx); For full features, please provide `MINERU_API_TOKEN`, which will quit flash mode.
- **Three transport modes** — `stdio`, `sse`, `streamable-http`

---

## Run from Source (Development)

```bash
git clone <repository-url>
cd mineru-mcp-server

uv pip install -e .

# stdio
uv run mineru-open-mcp

# streamable-http
uv run mineru-open-mcp --transport streamable-http --port 8001
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU cloud API token | — |
| `OUTPUT_DIR` | Directory for saved Markdown (and extra format) output | `~/mineru-downloads` |
| `ENABLE_LOG` | Set to `true` to write timestamped log files | disabled |
| `MINERU_LOG_DIR` | Override directory for log files | workspace `logs/` or `~/.mineru-open-mcp/logs/` |

**Log file location:** when `ENABLE_LOG=true`, logs are written to `~/.mineru-open-mcp/logs/log_<timestamp>.txt` (when installed) or `logs/` in the workspace root (when running from source). Override with `MINERU_LOG_DIR`:

```json
{
  "mcpServers": {
    "mineru": {
      "command": "mineru-open-mcp",
      "env": {
        "MINERU_API_TOKEN": "your_key_here",
        "ENABLE_LOG": "true",
        "MINERU_LOG_DIR": "/Users/you/mineru-logs"
      }
    }
  }
}
```

