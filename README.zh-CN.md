# MinerU Open API 命令行工具 (CLI)

[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/OpenDataLab/mineru-open-cli/blob/main/LICENSE)

**MinerU Open API CLI** 是一个完全免费、零依赖的命令行工具，只需一条命令，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

专为 **AI Agent**、**CI/CD 流水线** 以及需要在终端快速提取文档内容的**开发者**量身打造。

---

## 🚀 核心特性

- **零依赖**：单二进制文件，无需安装 Python、Node.js 等运行环境。
- **Agent 友好**：严格分离 stdout 和 stderr，支持管道调用，完美适配自动化工作流。
- **免登录模式**：使用 `flash-extract` 即可立刻获得结果，无需 API Token。
- **全功能模式**：支持 200MB/600页超大文档，完整保留版式、图片和公式。
- **批量处理**：支持通配符（glob）或文件列表 (`--list`) 处理成百上千的文件。

---

## 📦 安装指南

### Windows (PowerShell)
```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install/install.ps1 | iex
```

### Linux / macOS (Shell)
```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install/install.sh | sh
```

---

## 🛠️ 使用示例

### 1. 极速模式 (Flash Extract - 免登录，极速，仅 Markdown)
适合快速预览。无需配置 Token。限制：单文件 10MB/20页以内。
```bash
mineru-open-api flash-extract 报告.pdf
```

### 2. 全功能模式 (Full Feature Extract - 需登录)
支持超大文档 (200MB/600页)，完整保留版式和资源，支持多种格式输出。
```bash
# 首次运行请先配置 Token (或设置 MINERU_TOKEN 环境变量)
mineru-open-api auth

# 提取并输出 Markdown 到终端 (stdout)
mineru-open-api extract 论文.pdf

# 提取并保存所有资源 (图片/表格) 到指定目录
mineru-open-api extract 报告.pdf -o ./output/

# 导出为其他格式
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

### 3. 网页爬取 (Crawl)
将网页内容转换为高质量 Markdown。
```bash
mineru-open-api crawl https://www.baidu.com
```

### 4. 批量处理
```bash
# 批量处理当前目录下所有 PDF
mineru-open-api extract *.pdf -o ./results/

# 通过文件列表批量处理
mineru-open-api extract --list 文件列表.txt -o ./results/
```

---

## 🤖 AI Agent 自动化集成

MinerU CLI 为自动化而生。所有的状态信息均输出到 **stderr**，而文档内容则输出到 **stdout**。

**示例：将提取内容直接喂给其他工具**
```bash
export MINERU_TOKEN="your_token_here"
mineru-open-api extract paper.pdf | some-llm-tool
```

---

## ⚙️ 配置优先级

CLI 会按以下顺序查找 Token：
1. `--token` 命令行参数
2. `MINERU_TOKEN` 环境变量
3. `~/.mineru/config.yaml` 配置文件 (由 `mineru-open-api auth` 自动生成)

---

## 📄 开源协议
本项目采用 Apache-2.0 开源协议 - 详情请参阅 [LICENSE](LICENSE) 文件。

---

## 🔗 相关链接
- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
