<div align="center">

# MinerU-Ecosystem

**[MinerU](https://github.com/opendatalab/MinerU) Open API 官方生态工具集**

为开发者和 AI 智能体提供无缝的文档解析能力。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[English](README.md) | [中文](README.zh-CN.md)

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
├── mcp/           # Model Context Protocol 服务器（Python）
└── skills/               # AI 智能体技能（Claude Code、OpenClaw 等）
```

## 🔑 支持的 API

本仓库所有组件均适配 **两种** API 模式：

| 对比维度 | 🎯 精准解析 API | ⚡ Agent 轻量解析 API |
|---------|---------------|---------------------|
| 是否需要 Token | ✅ 需要 | ❌ 无需（IP 限频）|
| 模型版本 | `pipeline`（默认）/ `vlm`（推荐）/ `MinerU-HTML` | 固定 pipeline 轻量模型 |
| 表格/公式识别 | ✅ 支持（可配置）| ❌ 禁用（追求速度）|
| 文件大小限制 | ≤ 200MB | ≤ 10MB |
| 页数限制 | ≤ 600 页 | ≤ 20 页 |
| 批量支持 | ✅ 支持（≤ 200 个）| ❌ 单文件 |
| 输出格式 | Markdown、JSON、Zip，且可导出为 DOCX / HTML / LaTeX | 仅 Markdown |

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

### AI 智能体技能 (`skills/`)

- **[OpenClaw](https://clawhub.ai/MinerU-Extract/mineru-document-extractor)** — `在 clawhub 查看skills详情`
- **[CDN Link](https://webpub.shlab.tech/MinerU/skills/api/1.0.0.zip)** — 一键下载skill资源包
- 其他支持技能/工具接口的 AI 智能体（如 zeroclaw）

## 📚 相关文档

| 资源 | 链接 |
|---|---|
| MinerU Open API 文档 | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs) |
| MinerU 在线体验 | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU 开源项目 | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU) |

## 📄 开源许可

本项目基于 [Apache License 2.0](LICENSE) 开源。
