<div align="center">

# 🔮 MinerU-Ecosystem

**The official ecosystem toolkit for [MinerU](https://github.com/opendatalab/MinerU) Open API**

Empowering developers and AI agents with seamless document parsing capabilities.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[English](README.md) | [中文](README.zh-CN.md)

</div>

---

## 📖 Overview

**MinerU-Ecosystem** provides a full suite of tools, SDKs, and integrations built on top of the [MinerU Open API](https://mineru.net/apiManage/docs). Whether you're building production pipelines, integrating with LangChain for RAG, or enabling AI agents to parse documents on the fly — this repository has you covered.

[MinerU](https://github.com/opendatalab/MinerU) is an open-source, high-quality document extraction tool that converts unstructured documents (PDFs, images, Office files, etc.) into machine-readable Markdown and JSON.

## 🏗️ Repository Structure

```
MinerU-Ecosystem/
├── cli/                  # Command-line tool for document parsing
├── sdk/                  # Multi-language SDKs
│   ├── python/           #   Python SDK
│   ├── go/               #   Go SDK
│   └── typescript/       #   TypeScript SDK
├── mcp_server/           # Model Context Protocol server (Python)
└── skills/               # AI agent skills (Claude Code, OpenClaw, etc.)
```

## 🔑 Supported APIs

All components in this repository support **both** API modes:

| Comparison | 🎯 Precision Extract API | ⚡ Quick Parse API (Agent-Oriented) |
|---|---|---|
| Auth | ✅ Token required | ❌ Not required (IP rate-limited) |
| Model Versions | `pipeline` (default) / `vlm` (recommended) / `MinerU-HTML` | Fixed lightweight pipeline model |
| Table / Formula Recognition | ✅ Supported (configurable) | ❌ Disabled (speed-first) |
| File Size Limit | ≤ 200 MB | ≤ 10 MB |
| Page Limit | ≤ 600 pages | ≤ 20 pages |
| Batch Support | ✅ Supported (≤ 200 files) | ❌ Single file only |
| Output Formats | Markdown, JSON, Zip; optional export to DOCX / HTML / LaTeX | Markdown only |

## 🚀 Quick Start

### CLI (`cli/`)

A fast command-line tool for parsing documents directly from your terminal. Supports both Standard API and Quick Parse API.

#### Installation

**Windows (PowerShell)**

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

**Linux / macOS (Shell)**

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install/install.sh | sh
```

#### Usage

**1. Flash Extract (no login, fast, Markdown only)**

Great for quick previews. No Token needed. Limit: 10 MB / 20 pages per file.

```bash
mineru-open-api flash-extract report.pdf
```

**2. Precision Extract (login required)**

Supports large documents (200 MB / 600 pages), preserves layout and resources, multiple output formats.

```bash
# First-time setup: configure Token (or set MINERU_TOKEN env var)
mineru-open-api auth

# Extract and print Markdown to stdout
mineru-open-api extract paper.pdf

# Extract and save all resources (images/tables) to a directory
mineru-open-api extract report.pdf -o ./output/

# Export to other formats
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

**3. Web Crawl**

Convert web pages into high-quality Markdown.

```bash
mineru-open-api crawl https://www.example.com
```

**4. Batch Processing**

```bash
# Batch process all PDFs in the current directory
mineru-open-api extract *.pdf -o ./results/

# Batch process from a file list
mineru-open-api extract --list filelist.txt -o ./results/
```

### Python SDK

#### Installation

```bash
pip install mineru-open-sdk
```

#### Usage

**1. Flash Extract (no login, Markdown only)**

Great for quick previews. No Token needed.

```python
from mineru import MinerU

# Flash mode requires no Token
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

**2. Precision Extract (login required)**

Supports large files, rich assets (images/tables), and multiple output formats.

```python
from mineru import MinerU

# Get a free Token from https://mineru.net
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images)  # Get the list of extracted images
```

Multi-language SDKs are also available: **[Go](sdk/go/)** | **[TypeScript](sdk/typescript/)**. See the [`sdk/`](sdk/) directory for details.

### MCP Server (`mcp_server/`)

A [Model Context Protocol](https://modelcontextprotocol.io/) server implementation in Python, allowing MCP-compatible AI clients (such as Claude) to use MinerU's document parsing as a tool.

#### Configuration

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

### AI Agent Skills (`skills/`)

Pre-built skill for AI coding agents, enabling document extraction directly within agent workflows. The skill is wrapper by the `mineru-open-api` CLI and provides:

#### Skills Download

- **[OpenClaw](https://openclaw.com)** — View skill details on ClawHub
- **[LobeChat](TBD)** — Compatible via SKILL.md
- **[CDN Link](https://webpub.shlab.tech/MinerU/skills/api/0.1.0.zip)** — One-click download of the skill package
- Other AI agents that support skill/tool interfaces (e.g. ZeroClaw)


## 📚 Documentation

| Resource | Link |
|---|---|
| MinerU Open API Docs | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs) |
| MinerU Online Demo | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU Open Source Project | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).