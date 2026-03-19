<div align="center">

# 🔮 MinerU-Ecosystem

**The official ecosystem toolkit for [MinerU](https://github.com/opendatalab/MinerU) SaaS API**

Empowering developers and AI agents with seamless document parsing capabilities.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![API Docs](https://img.shields.io/badge/API%20Docs-mineru.net-green)](https://mineru.net/apiManage/docs)

[English](#-overview) | [中文](#-项目简介)

</div>

---

## 📖 Overview

**MinerU-Ecosystem** provides a full suite of tools, SDKs, and integrations built on top of the [MinerU SaaS API](https://mineru.net/apiManage/docs). Whether you're building production pipelines, integrating with LangChain for RAG, or enabling AI agents to parse documents on the fly — this repository has you covered.

[MinerU](https://github.com/opendatalab/MinerU) is an open-source, high-quality document extraction tool that converts unstructured documents (PDFs, images, Office files, etc.) into machine-readable Markdown and JSON.

## 🏗️ Repository Structure

```
MinerU-Ecosystem/
├── cli/                  # Command-line tool for document parsing
├── sdk/                  # Multi-language SDKs
│   ├── python/           #   Python SDK
│   ├── go/               #   Go SDK
│   └── typescript/       #   TypeScript SDK
├── langchain-mineru/     # LangChain RAG integration plugin
├── mcp_server/           # Model Context Protocol server (Python)
└── skills/               # AI agent skills (Claude Code, OpenClaw, etc.)
```

## 🔑 Supported APIs

All components in this repository support **both** API modes:

### 📋 Standard API

> Full-featured document parsing with authentication.

| Item | Details |
|---|---|
| **Auth** | API token required ([apply here](https://mineru.net/apiManage/token)) |
| **Input Formats** | PDF, HTML, Images (PNG/JPG/JPEG/JP2/WEBP/GIF/BMP), Word (DOC/DOCX), PowerPoint (PPT/PPTX) |
| **File Limits** | Max **200 MB** per file, max **600** pages |
| **Output Formats** | Markdown + JSON |

### ⚡ Quick Parse API (Agent-Oriented)

> Lightweight, no-login-required API designed for AI agents and rapid prototyping.

| Item | Details |
|---|---|
| **Auth** | **Not required** (no login needed) |
| **Input Formats** | PDF, Images (PNG/JPG/JPEG/JP2/WEBP/GIF/BMP), Word (DOCX), PowerPoint (PPTX), Excel (XLS/XLSX) |
| **File Limits** | max **10 MB** per file, PDF: max **20** pages |
| **Output Format** | Markdown only |

## 🚀 Quick Start

### CLI

```bash
# TODO: CLI usage example coming soon
```

### Python SDK

```python
# TODO: Python SDK usage example coming soon
```

### LangChain Integration

```python
# TODO: LangChain-MinerU usage example coming soon
```

## 📦 Components

### CLI (`cli/`)

A fast command-line tool for parsing documents directly from your terminal. Supports both Standard API and Quick Parse API.

### SDKs (`sdk/`)

Multi-language SDKs for seamless integration into your application:

- **Python** — Idiomatic Python client with async support
- **Go** — High-performance Go client
- **TypeScript** — Type-safe client for Node.js and browser environments

### LangChain Plugin (`langchain-mineru/`)

A [LangChain](https://www.langchain.com/) document loader and RAG plugin powered by MinerU, enabling:

- Document loading and parsing via MinerU API
- Integration with LangChain vector stores and retrieval chains
- Seamless RAG workflow for AI applications

### MCP Server (`mcp_server/`)

A [Model Context Protocol](https://modelcontextprotocol.io/) server implementation in Python, allowing MCP-compatible AI clients (such as Claude) to use MinerU's document parsing as a tool.

### AI Agent Skills (`skills/`)

Pre-built skill for AI coding agents, enabling document extraction directly within agent workflows. The skill is wrapper by the `mineru-open-api` CLI and provides:

#### Skills Download

- **[OpenClaw](https://openclaw.com)** — `View skill details on ClawHub`
- **[lobeChat](TBD)** — Compatible via SKILL.md
- **[CDN Link](https://webpub.shlab.tech/MinerU/skills/api/0.1.0.zip)** — One-click download skill package
- Other AI agents like zeroclaw that also support skill/tool interfaces


## 📚 Documentation

| Resource | Link |
|---|---|
| MinerU SaaS API Docs | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs) |
| MinerU Open Source Project | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">

# 🔮 MinerU-Ecosystem

**[MinerU](https://github.com/opendatalab/MinerU) SaaS API 官方生态工具集**

为开发者和 AI 智能体提供无缝的文档解析能力。

</div>

## 📖 项目简介

**MinerU-Ecosystem** 提供基于 [MinerU SaaS API](https://mineru.net/apiManage/docs) 构建的完整工具套件、SDK 和集成方案。无论你是构建生产级的文档处理流水线、集成 LangChain 实现 RAG，还是让 AI 智能体实时解析文档——本仓库都能满足你的需求。

[MinerU](https://github.com/opendatalab/MinerU) 是一款开源、高质量的文档提取工具，能将非结构化文档（PDF、图片、Office 文件等）转换为机器可读的 Markdown 和 JSON 格式。

## 🏗️ 仓库结构

```
MinerU-Ecosystem/
├── cli/                  # 命令行工具
├── sdk/                  # 多语言 SDK
│   ├── python/           #   Python SDK
│   ├── go/               #   Go SDK
│   └── typescript/       #   TypeScript SDK
├── langchain-mineru/     # LangChain RAG 集成插件
├── mcp_server/           # Model Context Protocol 服务器（Python）
└── skills/               # AI 智能体技能（Claude Code、OpenClaw 等）
```

## 🔑 支持的 API

本仓库所有组件均适配 **两种** API 模式：

### 📋 标准 API

> 功能完整的文档解析服务，需要鉴权认证。

| 项目 | 详情 |
|---|---|
| **鉴权方式** | 需要 API Token（[申请地址](https://mineru.net/apiManage/token)） |
| **支持格式** | PDF、HTML、图片（PNG/JPG/JPEG/JP2/WEBP/GIF/BMP）、Word（DOC/DOCX）、PowerPoint（PPT/PPTX） |
| **文件限制** | 单文件最大 **200 MB**，最多 **600** 页 |
| **输出格式** | Markdown + JSON |

### ⚡ 快速解析 API（面向 Agent）

> 轻量级免登录接口，专为 AI 智能体和快速原型设计而生。

| 项目 | 详情 |
|---|---|
| **鉴权方式** | **无需登录** |
| **支持格式** | PDF、图片（PNG/JPG/JPEG/JP2/WEBP/GIF/BMP）、Word（DOCX）、PowerPoint（PPTX）、Excel（XLS/XLSX） |
| **文件限制** | 单文件最大 **10 MB**，PDF：最多 **20** 页 |
| **输出格式** | 仅 Markdown |

## 🚀 快速开始

### CLI

```bash
# TODO: CLI 使用示例即将补充
```

### Python SDK

```python
# TODO: Python SDK 使用示例即将补充
```

### LangChain 集成

```python
# TODO: LangChain-MinerU 使用示例即将补充
```

## 📦 核心组件

### CLI 命令行工具 (`cli/`)

高效的命令行工具，可直接在终端中解析文档。支持标准 API 和快速解析 API。

### SDK (`sdk/`)

多语言 SDK，无缝集成到你的应用中：

- **Python** — 符合 Python 风格的客户端，支持异步
- **Go** — 高性能 Go 客户端
- **TypeScript** — 类型安全的客户端，适用于 Node.js 和浏览器环境

### LangChain 插件 (`langchain-mineru/`)

基于 MinerU 的 [LangChain](https://www.langchain.com/) 文档加载器和 RAG 插件，支持：

- 通过 MinerU API 进行文档加载和解析
- 与 LangChain 向量存储和检索链集成
- 为 AI 应用提供无缝的 RAG 工作流

### MCP 服务器 (`mcp_server/`)

基于 Python 的 [Model Context Protocol](https://modelcontextprotocol.io/) 服务器实现，允许 MCP 兼容的 AI 客户端（如 Claude）将 MinerU 文档解析作为工具使用。

### AI 智能体技能 (`skills/`)

为 AI 编程智能体预构建的文档解析技能，封装 `mineru-open-api` CLI。

#### Skills 下载

- **[OpenClaw](https://openclaw.com)** — `在 clawhub 查看skills详情`
- **[lobeChat](待定)** — 通过 SKILL.md 兼容
- **[CDN Link](https://webpub.shlab.tech/MinerU/skills/api/0.1.0.zip)** — 一键下载skill资源包
- 其他支持技能/工具接口的 AI 智能体（如 zeroclaw）

## 📚 相关文档

| 资源 | 链接 |
|---|---|
| MinerU SaaS API 文档 | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs) |
| MinerU 开源项目 | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

## 📄 开源许可

本项目基于 [Apache License 2.0](LICENSE) 开源。
