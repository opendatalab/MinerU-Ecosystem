<div align="center">

# MinerU-Ecosystem

**[MinerU](https://github.com/opendatalab/MinerU) Open API 官方生态工具集**

为开发者和 AI 智能体提供无缝的文档解析能力。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[English Document](README.md)

</div>

---

## 📖 项目简介

**MinerU-Ecosystem** 提供基于 [MinerU Open API](https://mineru.net/apiManage/docs) 构建的完整工具套件、SDK 和集成方案。无论你是构建生产级的文档处理流水线、集成 LangChain 实现 RAG，还是让 AI 智能体实时解析文档——本仓库都能满足你的需求。

[MinerU](https://github.com/opendatalab/MinerU) 是一款开源、高质量的文档提取工具，能将非结构化文档（PDF、图片、Office 文件等）转换为机器可读的 Markdown 和 JSON 格式。

## 🏗️ 仓库结构

```
MinerU-Ecosystem/
├── cli/                  # 命令行工具
├── sdk/                  # 多语言 SDK
│   ├── python/           #   Python SDK
│   ├── go/               #   Go SDK
│   └── typescript/       #   TypeScript SDK
├── langchain_mineru/     # LangChain 文档加载器集成
├── llama-index-readers-mineru/     # LlamaIndex 文档解析器集成
├── mcp/                  # Model Context Protocol 服务器（Python）
└── skills/               # AI 智能体技能（Claude Code、OpenClaw 等）
```

## 🔑 支持的 API

本仓库所有组件均适配 **两种** API 模式：

| 对比维度       | 🎯 精准解析 API                                     | ⚡ Agent 轻量解析 API  |
| -------------- | --------------------------------------------------- | ---------------------- |
| 是否需要 Token | ✅ 需要                                             | ❌ 无需（IP 限频）     |
| 模型版本       | `pipeline`（默认）/ `vlm`（推荐）/ `MinerU-HTML`    | 固定 pipeline 轻量模型 |
| 文件大小限制   | ≤ 200MB                                             | ≤ 10MB                 |
| 页数限制       | ≤ 600 页                                            | ≤ 20 页                |
| 批量支持       | ✅ 支持（≤ 200 个）                                 | ❌ 单文件              |
| 输出格式       | Markdown、JSON、Zip，且可导出为 DOCX / HTML / LaTeX | 仅 Markdown            |

## 🧭 按使用场景选择接入方式

不确定该从哪里开始时，先按你的目标选择路径：

```text
我想要……
│
├── 🌐 立即体验，不安装也不写代码
│   └── Web App → https://mineru.net/OpenSourceTools/Extractor
│
├── 💻 在终端里直接解析文档
│   └── CLI → cli/
│       flash-extract：免 Token，适合快速预览
│       extract：功能完整，适合生产处理
│
├── 🐍 集成到 Python / Go / TypeScript 项目
│   └── SDK → sdk/python/ | sdk/go/ | sdk/typescript/
│
├── 🤖 让 AI Agent 具备文档解析能力
│   ├── 直接调用命令行工具 → cli/
│   ├── 自然语言技能接入（OpenClaw、ZeroClaw 等）→ skills/
│   └── 标准 MCP 协议接入（Cursor、Claude Desktop、Windsurf 等）→ mcp/
│
├── 📚 搭建 RAG / 知识库
│   ├── LangChain Loader → langchain_mineru/
│   └── LlamaIndex Reader → llama-index-readers-mineru/
│       flash 模式：零 Token，快速起步
│       precision 模式：支持 OCR、表格、公式等更完整能力
```

如果你只是想先验证效果，优先从 Web App 或 `flash` 模式开始；如果你已经进入正式集成阶段，需要更高精度、OCR、表格和公式识别，优先选择 `precision` 模式。

## 🚀 快速开始

### CLI (`cli/`)

高效的命令行工具，可直接在终端中解析文档。支持标准 API 和快速解析 API。

#### 安装

**Windows (PowerShell)**

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

**Linux / macOS (Shell)**

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

#### 使用示例

**1. Agent 轻量解析（免登录，极速，仅 Markdown）**

```bash
mineru-open-api flash-extract 报告.pdf
```

**2. 精准解析（需登录）**

```bash
# 首次运行请先配置 Token（或设置 MINERU_TOKEN 环境变量）
mineru-open-api auth

# 提取并输出 Markdown 到终端 (stdout)
mineru-open-api extract 论文.pdf

# 提取并保存所有资源（图片/表格）到指定目录
mineru-open-api extract 报告.pdf -o ./output/

# 导出为其他格式
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

**3. 网页爬取（Crawl）**

将网页内容转换为高质量 Markdown。

```bash
mineru-open-api crawl https://www.baidu.com
```

**4. 批量处理**

```bash
# 批量处理当前目录下所有 PDF
mineru-open-api extract *.pdf -o ./results/

# 通过文件列表批量处理
mineru-open-api extract --list 文件列表.txt -o ./results/
```

### Python SDK

#### 安装

```bash
pip install mineru-open-sdk
```

#### 使用示例

**1. Agent 轻量解析（免登录，仅 Markdown）**

适合快速预览。无需配置 Token。

```python
from mineru import MinerU

# 极速模式无需传入 Token
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

**2. 精准解析（需登录）**

支持超大文件、丰富的资产（图片/表格）及多种输出格式。

```python
from mineru import MinerU

# 从 https://mineru.net 获取免费 Token
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images)  # 获取提取出的图片列表
```

多语言 SDK 同样可用：**[Go](sdk/go/)** | **[TypeScript](sdk/typescript/)**，详见 [`sdk/`](sdk/) 目录。

### AI 智能体技能 (`skills/`)

- **[OpenClaw](https://clawhub.ai/MinerU-Extract/mineru-ai)** — `在 clawhub 查看skills详情`
- **[CDN Link](https://cdn-mineru.openxlab.org.cn/open-api-cli/skill.zip)** — 一键下载skill资源包
- 其他支持技能/工具接口的 AI 智能体（如 zeroclaw）

### MCP 服务器 (`mcp/`)

基于 Python 的 [Model Context Protocol](https://modelcontextprotocol.io/) 服务器实现，允许 MCP 兼容的 AI 客户端（如 Claude）将 MinerU 文档解析作为工具使用。

#### 配置示例

**使用 `uvx`（推荐 — 始终运行最新版本）：**

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

### LangChain 集成 (`langchain_mineru/`)

一个 LangChain 文档加载器，可将 PDF、Word、PPT、图片等文档解析为 LangChain 兼容的 `Document` 对象，便于直接接入切分、向量化与检索流程。

#### 安装

```bash
pip install langchain-mineru
```

#### 使用

**1. 基础用法（默认 `flash` 模式，无需 Token）**

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="demo.pdf")
docs = loader.load()

print(docs[0].page_content[:500])
print(docs[0].metadata)
```

默认使用 `mode="flash"`，适合快速预览和轻量解析。

**2. Precision 模式（需 Token）**

适合扫描件、长文档，以及对 OCR、表格、公式识别要求更高的场景。

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/manual.pdf",
    mode="precision",
    token="your-api-token",  # 或设置 MINERU_TOKEN 环境变量
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

**3. 接入 LangChain RAG 流水线**

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
results = vs.similarity_search("这个文档的核心结论是什么？", k=3)
for r in results:
    print(r.page_content[:200])
```

默认使用 `mode="flash"`（无需 API Token）；切换到 `mode="precision"` 可获得更高精度的解析结果（需要 Token 认证）。如果用于 RAG，建议对 PDF 开启 `split_pages=True`，这样可以得到更细粒度的页级 `Document`。

### LlamaIndex 集成 (`llama-index-readers-mineru/`)

一个面向 LlamaIndex 的文档读取器，可将 PDF、Word、PPT、图片、Excel 等文件通过 MinerU 解析为 LlamaIndex 兼容的 `Document` 对象，便于直接接入索引与检索流程。

#### 安装

```bash
pip install llama-index-readers-mineru
```

#### 使用

**1. Flash 模式（默认，无需 Token）**

适合快速接入和轻量解析，返回 Markdown 结果。

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader()
documents = reader.load_data("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(documents[0].text[:500])
print(documents[0].metadata)
```

**2. Precision 模式（需 Token）**

适合扫描件、长文档以及对表格、公式识别要求更高的场景。可通过参数启用 OCR、公式和表格识别。

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(
    mode="precision",
    token="your-api-token",  # 或设置 MINERU_TOKEN 环境变量
    ocr=True,
    formula=True,
    table=True,
    pages="1-20",
)
documents = reader.load_data("/path/to/paper.pdf")
```

**3. 直接接入 LlamaIndex 索引**

```python
from llama_index.core import VectorStoreIndex
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(split_pages=True)
documents = reader.load_data("/path/to/paper.pdf")

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("总结这篇文档的核心结论")
print(response)
```

默认使用 `mode="flash"`，无需 Token；切换为 `mode="precision"` 后需要先在 `https://mineru.net` 申请 Token。若用于 RAG，建议开启 `split_pages=True` 获取更细粒度的页级 `Document`。

## 📚 相关文档

| 资源                 | 链接                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| MinerU Open API 文档 | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs)                       |
| MinerU 在线体验      | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU 开源项目      | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)               |

## 📄 开源许可

本项目基于 [Apache License 2.0](LICENSE) 开源。
