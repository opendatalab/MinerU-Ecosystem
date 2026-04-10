<div align="center">

# MinerU-Ecosystem

**The official ecosystem toolkit for [MinerU](https://github.com/opendatalab/MinerU) Open API**

Empowering developers and AI agents with seamless document parsing capabilities.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[中文文档](README.zh-CN.md)

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
├── langchain_mineru/     # LangChain document loader integration
├── llama-index-readers-mineru/     # LlamaIndex document reader integration
├── mcp/                  # Model Context Protocol server (Python)
└── skills/               # AI agent skills (Claude Code, OpenClaw, etc.)
```

## 🔑 Supported APIs

All components in this repository support **both** API modes:

| Comparison      | 🎯 Precision Extract API                                    | ⚡ Quick Parse API (Agent-Oriented) |
| --------------- | ----------------------------------------------------------- | ----------------------------------- |
| Auth            | ✅ Token required                                           | ❌ Not required (IP rate-limited)   |
| Model Versions  | `pipeline` (default) / `vlm` (recommended) / `MinerU-HTML`  | Fixed lightweight pipeline model    |
| File Size Limit | ≤ 200 MB                                                    | ≤ 10 MB                             |
| Page Limit      | ≤ 600 pages                                                 | ≤ 20 pages                          |
| Batch Support   | ✅ Supported (≤ 200 files)                                  | ❌ Single file only                 |
| Output Formats  | Markdown, JSON, Zip; optional export to DOCX / HTML / LaTeX | Markdown only                       |

## 🧭 Choose Your Integration Path

Not sure where to start? Pick the path that matches your use case:

```text
I want to...
│
├── 🌐 Try it instantly, with no install and no code
│   └── Web App → https://mineru.net/OpenSourceTools/Extractor
│
├── 💻 Parse documents from the terminal
│   └── CLI → cli/
│       flash-extract: no token, best for quick previews
│       extract: full features, better for production workflows
│
├── 🐍 Integrate it into my Python / Go / TypeScript project
│   └── SDK → sdk/python/ | sdk/go/ | sdk/typescript/
│
├── 🤖 Enable my AI agent to parse documents
│   ├── Call the CLI directly → cli/
│   ├── Use natural-language skills (OpenClaw, ZeroClaw, etc.) → skills/
│   └── Use MCP protocol (Cursor, Claude Desktop, Windsurf, etc.) → mcp/
│
├── 📚 Build a RAG pipeline / knowledge base
│   ├── LangChain Loader → langchain_mineru/
│   └── LlamaIndex Reader → llama-index-readers-mineru/
│       flash mode: zero-token quick start
│       precision mode: OCR, tables, formulas, and higher fidelity
```

If you just want to validate the parsing quality, start with the Web App or `flash` mode. If you are moving into a production integration and need OCR, table extraction, or formula recognition, use `precision` mode.

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
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
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

### AI Agent Skills (`skills/`)

Pre-built skill for AI coding agents, enabling document extraction directly within agent workflows. The skill is wrapper by the `mineru-open-api` CLI and provides:

#### Skills Download

- **[OpenClaw](https://clawhub.ai/MinerU-Extract/mineru-ai)** — `View skill details on ClawHub`
- **[CDN Link](https://cdn-mineru.openxlab.org.cn/open-api-cli/skill.zip)** — One-click download skill package
- Other AI agents like zeroclaw that also support skill/tool interfaces

### MCP Server (`mcp/`)

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

### LangChain Integration (`langchain_mineru/`)

A LangChain Document Loader that converts PDFs, Word files, PPTs, images, and other documents into LangChain-compatible `Document` objects, ready for splitting, embedding, and retrieval.

#### Installation

```bash
pip install langchain-mineru
```

#### Usage

**1. Basic usage (`flash` mode by default, no token required)**

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="demo.pdf")
docs = loader.load()

print(docs[0].page_content[:500])
print(docs[0].metadata)
```

Default is `mode="flash"`, which is ideal for quick previews and lightweight integrations.

**2. Precision mode (token required)**

Best for scanned PDFs, long documents, and workflows that need OCR, table extraction, or formula recognition.

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/manual.pdf",
    mode="precision",
    token="your-api-token",  # or set MINERU_TOKEN
    split_pages=True,
    pages="1-5",
    ocr=True,
    formula=True,
    table=True,
)

docs = loader.load()
for doc in docs:
    print(doc.metadata.get("page"), doc.page_content[:200])
```

**3. Mixed local and remote sources**

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source=[
        "/path/to/demo_a.pdf",
        "/path/to/demo_b.docx",
        "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    ]
)

docs = loader.load()
for doc in docs:
    print(doc.metadata["source"], "-", doc.page_content[:100])
```

**4. Use it in a LangChain RAG pipeline**

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(source="demo.pdf", split_pages=True)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("What are the key conclusions in this document?", k=3)
for r in results:
    print(r.page_content[:200])
```

Default is `mode="flash"` (no API token required). Switch to `mode="precision"` for higher fidelity with token auth. For RAG use cases, `split_pages=True` is usually a better default for PDFs because it gives you page-level `Document` granularity.

### LlamaIndex Integration (`llama-index-readers-mineru/`)

A document reader for LlamaIndex that parses PDFs, Word files, PPTs, images, and Excel files through MinerU and returns LlamaIndex-compatible `Document` objects for indexing and retrieval.

#### Installation

```bash
pip install llama-index-readers-mineru
```

#### Usage

**1. Flash mode (default, no token required)**

Good for quick setup and lightweight parsing. Output is returned as Markdown.

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader()
documents = reader.load_data("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(documents[0].text[:500])
print(documents[0].metadata)
```

**2. Precision mode (token required)**

Best for scanned files, longer documents, and use cases that need OCR, formula parsing, or table recognition.

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(
    mode="precision",
    token="your-api-token",  # or set MINERU_TOKEN
    ocr=True,
    formula=True,
    table=True,
    pages="1-20",
)
documents = reader.load_data("/path/to/paper.pdf")
```

**3. Use it in a LlamaIndex pipeline**

```python
from llama_index.core import VectorStoreIndex
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(split_pages=True)
documents = reader.load_data("/path/to/paper.pdf")

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("Summarize the main findings of this document")
print(response)
```

Default is `mode="flash"` with no token required. Switch to `mode="precision"` when you need higher parsing fidelity. For PDF-based RAG pipelines, `split_pages=True` is recommended so each page becomes a separate `Document`.

## 📚 Documentation

| Resource                   | Link                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------ |
| MinerU Open API Docs       | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs)                       |
| MinerU Online Demo         | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU Open Source Project | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)               |

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).
