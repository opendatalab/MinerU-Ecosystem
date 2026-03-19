# MinerU Open API CLI

[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/cli/blob/main/LICENSE)
[![Go Report Card](https://goreportcard.com/badge/github.com/opendatalab/MinerU-Ecosystem/cli)](https://goreportcard.com/report/github.com/opendatalab/MinerU-Ecosystem/cli)

**MinerU Open API CLI** is a completely free, zero-dependency command-line tool designed to turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown. 

Designed for **AI Agents**, **CI/CD Pipelines**, and **Developers** who need a blazing fast, "no-fuss" document-to-markdown solution.

---

## 🚀 Key Features

- **Zero Dependency**: Single binary, no Python/Node.js environment required.
- **Agent Friendly**: Clean stdout/stderr separation, easy to pipe and automate.
- **No Auth Mode**: Use `flash-extract` for instant results without any API token.
- **Full Featured**: Advanced extraction with layout preservation, images, and formula support.
- **Batch Processing**: Process hundreds of files via globbing or file lists (`--list`).

---

## 📦 Installation

### Windows (PowerShell)
```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install/install.ps1 | iex
```

### Linux / macOS (Shell)
```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install/install.sh | sh
```

---

## 🛠️ Usage

### 1. Flash Extract (Fast, No Auth, Markdown-only)
Ideal for quick previews. No token required. Limited to 10MB and 20 pages.
```bash
mineru-open-api flash-extract report.pdf
```

### 2. Full Feature Extract (Auth Required)
Supports large files (up to 200MB/600 pages), layout preservation, and multiple formats.
```bash
# Authenticate first (or set MINERU_TOKEN env)
mineru-open-api auth

# Extract to stdout (Markdown)
mineru-open-api extract report.pdf

# Extract and save all assets (images/tables) to a directory
mineru-open-api extract report.pdf -o ./output/

# Convert to other formats
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

### 3. Web Crawling
Convert any web page to clean Markdown.
```bash
mineru-open-api crawl https://www.baidu.com
```

### 4. Batch Processing
```bash
# Process all PDFs in a directory
mineru-open-api extract *.pdf -o ./results/

# Process from a list file
mineru-open-api extract --list files.txt -o ./results/
```

---

## 🤖 Integration for AI Agents

MinerU CLI is built for automation. All status messages go to **stderr**, while the document content goes to **stdout**.

**Example: Piping content to another tool**
```bash
export MINERU_TOKEN="your_token_here"
mineru-open-api extract paper.pdf | some-llm-tool
```

---

## ⚙️ Configuration

The CLI looks for tokens in the following order:
1. `--token` flag
2. `MINERU_TOKEN` environment variable
3. `~/.mineru/config.yaml` (created by `mineru-open-api auth`)

---

## 📄 License
This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links
- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/docs)
