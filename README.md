<div align="center">

# MinerU-Ecosystem

**The official ecosystem toolkit for [MinerU](https://github.com/opendatalab/MinerU) Open API**

Empowering developers and AI agents with seamless document parsing capabilities — PDF · Word · PPT · Images · Web pages → Markdown / JSON · VLM+OCR dual engine · 109 languages · MCP Server · LangChain / RAGFlow / Dify / FastGPT native integration.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[中文文档](README.zh-CN.md)

</div>

---

## 📖 Overview

**MinerU-Ecosystem** provides a full suite of tools, SDKs, and integrations built on top of the [MinerU Open API](https://mineru.net/apiManage/docs). Whether you're building production pipelines, integrating with LangChain for RAG, or enabling AI agents to parse documents on the fly — this repository has you covered.

[MinerU](https://github.com/opendatalab/MinerU) is an open-source, high-accuracy document parsing engine that converts unstructured documents (PDFs, images, Office files, etc.) into machine-readable Markdown and JSON, purpose-built for LLM pre-training, RAG, and agentic workflows.

**Core capabilities:**
- Formulas → LaTeX · Tables → HTML, accurate complex layout reconstruction
- Supports scanned docs, handwriting, multi-column layouts, cross-page table merging
- Output follows human reading order with automatic header/footer removal
- VLM + OCR dual engine, 109-language OCR recognition

---

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

---

## 🔑 Supported APIs

All components support both API modes:

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

---

## 🚀 Quick Start

### 💻 CLI (`cli/`)

A fast command-line tool for parsing documents directly from your terminal.

#### Installation

```bash
# Linux / macOS
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

```powershell
# Windows (PowerShell)
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

**Flash Extract (no login)**

```bash
mineru-open-api flash-extract report.pdf
```

**Precision Extract (login required)**

```bash
# First-time setup
mineru-open-api auth

# Extract to stdout
mineru-open-api extract paper.pdf

# Save all resources (images/tables) to directory
mineru-open-api extract report.pdf -o ./output/

# Export to multiple formats
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

**Web Crawl**

```bash
mineru-open-api crawl https://www.example.com
```

**Batch Processing**

```bash
# All PDFs in current directory
mineru-open-api extract *.pdf -o ./results/

# From a file list
mineru-open-api extract --list filelist.txt -o ./results/
```

---

### 🐍 Python SDK

#### Installation

```bash
pip install mineru-open-sdk
```

**Flash Extract (no token)**

```python
from mineru import MinerU

client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
```

**Precision Extract (token required)**

```python
from mineru import MinerU

client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
print(result.images)  # extracted image list
```

---

### 🐹 Go SDK

#### Installation

```bash
go get github.com/opendatalab/MinerU-Ecosystem/sdk/go@latest
```

**Flash Extract**

```go
package main

import (
    "context"
    "fmt"
    mineru "github.com/opendatalab/MinerU-Ecosystem/sdk/go"
)

func main() {
    client := mineru.NewFlash()
    result, err := client.FlashExtract(
        context.Background(),
        "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    )
    if err != nil {
        panic(err)
    }
    fmt.Println(result.Markdown)
}
```

**Precision Extract**

```go
client, err := mineru.New("your-api-token")
if err != nil {
    panic(err)
}
result, err := client.Extract(
    context.Background(),
    "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
)
if err != nil {
    panic(err)
}
fmt.Println(result.Markdown)
```

**Precision Extract with options**

```go
result, err := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),
    mineru.WithLanguage("en"),
    mineru.WithPages("1-20"),
    mineru.WithExtraFormats("docx"),
    mineru.WithPollTimeout(10*time.Minute),
)
if err != nil {
    panic(err)
}
if err := result.SaveAll("./output"); err != nil {
    panic(err)
}
```

**Batch Processing**

```go
ch, err := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
if err != nil {
    panic(err)
}
for result := range ch {
    fmt.Printf("%s: %s\n", result.Filename, result.State)
}
```

**Web Crawling**

```go
result, err := client.Crawl(ctx, "https://www.example.com")
if err != nil {
    panic(err)
}
fmt.Println(result.Markdown)
```

---

### 🟦 TypeScript / JavaScript SDK

#### Installation

```bash
npm install mineru-open-sdk
```

**Flash Extract**

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU();
const result = await client.flashExtract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
);
console.log(result.markdown);
```

**Precision Extract**

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU("your-api-token");
const result = await client.extract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
);
console.log(result.markdown);
console.log(result.images);
```

**Precision Extract with options**

```typescript
import { MinerU, saveAll } from "mineru-open-sdk";

const client = new MinerU("your-api-token");
const result = await client.extract("./paper.pdf", {
  model: "vlm",       // "vlm" | "pipeline" | "html"
  language: "en",
  pages: "1-20",
  extraFormats: ["docx"],
  timeout: 600,
});
await saveAll(result, "./output");
```

**Batch Processing**

```typescript
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: ${result.state}`);
}
```

**Web Crawling**

```typescript
const result = await client.crawl("https://www.example.com");
console.log(result.markdown);
```

---

## 🤖 Use with Claude / Cursor (MCP Server)

MinerU provides an official MCP Server allowing Claude Desktop, Cursor, Windsurf, and any MCP-compatible AI client to parse documents as a native tool.

> No API key needed — Flash mode works out of the box, free, up to 20 pages / 10 MB per file.

**Configure: `claude_desktop_config.json` / `.cursor/mcp.json`**

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

**Streamable HTTP mode (web-based MCP clients)**

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

**Tools exposed via MCP:**

| Tool | Description |
|---|---|
| `parse_documents` | Convert PDF, DOCX, PPTX, images, HTML to Markdown |
| `get_ocr_languages` | List all 109 supported OCR languages |
| `clean_logs` | Delete old server log files (when `ENABLE_LOG=true`) |

**Environment Variables:**

| Variable | Description | Default |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU cloud API token | — |
| `OUTPUT_DIR` | Directory for saved output | `~/mineru-downloads` |
| `ENABLE_LOG` | Set `true` to write log files | disabled |
| `MINERU_LOG_DIR` | Override log file directory | `~/.mineru-open-mcp/logs/` |

---

## 🦜 Use in RAG with LangChain

`langchain-mineru` is an official LangChain Document Loader — parse any document into LangChain `Document` objects with one line of code.

#### Installation

```bash
pip install langchain-mineru
```

**Minimal example (no token)**

**1. Basic usage (`flash` mode by default, no token required)**

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="demo.pdf")   # flash mode, no token needed
docs = loader.load()
print(docs[0].page_content[:500])
print(docs[0].metadata)
```

Default is `mode="flash"`, which is ideal for quick previews and lightweight integrations.

**2. Precision mode (token required)**

Best for long documents, larger files, and workflows that need higher-fidelity extraction or standard API outputs. Flash mode also supports OCR, table, and formula switches within flash API limits.

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/manual.pdf",
    mode="precision",
    token="your-api-token",  # or set MINERU_TOKEN
    split_pages=True,
    pages="1-5",
)

docs = loader.load()
for doc in docs:
    print(doc.metadata.get("page"), doc.page_content[:200])
```

**3. Use it in a LangChain RAG pipeline**

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

### ## Use in RAG with LlamaIndex

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

Best for longer documents, larger files, and use cases that need higher-fidelity extraction or standard API outputs. Flash mode also supports OCR, formula, and table switches within flash API limits.

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(
    mode="precision",
    token="your-api-token",  # or set MINERU_TOKEN
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

---

## 🤖 AI Agent Skills (`skills/`)

Pre-built skills for AI coding agents, wrapping the `mineru-open-api` CLI for use in agent workflows.

- **[OpenClaw / ClawHub](https://clawhub.ai/MinerU-Extract/mineru-ai)** — View skill details
- **[One-click download](https://cdn-mineru.openxlab.org.cn/open-api-cli/skill.zip)** — Skill package
- Compatible with Claude Code, OpenClaw, ZeroClaw, and other skill-interface agents

---

## 🔗 All Integrations

| Framework / Tool | Status | Notes |
|---|---|---|
| LangChain | ✅ Official | `pip install langchain-mineru` |
| LlamaIndex | ✅ Community | See MinerU-Ecosystem |
| RAGFlow | ✅ Supported | Document loader integration |
| RAG-Anything | ✅ Supported | Multi-modal RAG pipeline |
| Flowise | ✅ Supported | Node-based RAG builder |
| Dify | ✅ Native Plugin | Built-in document loader |
| FastGPT | ✅ Native Plugin | Integration guide |
| Claude Desktop | ✅ MCP | `uvx mineru-open-mcp` |
| Cursor | ✅ MCP | `.cursor/mcp.json` config |
| Windsurf | ✅ MCP | stdio / streamable-http |
| OpenClaw / ZeroClaw | ✅ Agent Skill | ClawHub |
| Go SDK | ✅ Official | `go get .../sdk/go@latest` |
| TypeScript SDK | ✅ Official | `npm install mineru-open-sdk` |
| Python SDK | ✅ Official | `pip install mineru-open-sdk` |

---

## 📚 Documentation

| Resource | Link |
|---|---|
| MinerU Open API Docs | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs) |
| MinerU Online Demo | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU Open Source | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).
