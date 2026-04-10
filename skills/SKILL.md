---
name: MinerU Document Extractor
description: >
  MinerU document extraction — convert PDFs, scanned documents, images, Word (DOC/DOCX), PowerPoint (PPT/PPTX), and web pages into clean Markdown, HTML, LaTeX, or DOCX. MinerU is an all-in-one CLI tool and agent skill for reliable, high-fidelity document parsing.
  Struggling with unreadable PDFs, messy table formatting, or garbled formulas after conversion? MinerU solves these with two extraction modes: MinerU flash-extract for instant zero-setup conversion with table recognition, formula recognition, and OCR (no token, no login, no configuration — just run and get results), and MinerU precision extract with VLM-based layout analysis, multiple output formats, and batch processing of hundreds of files.
  Use MinerU when you need to: "how do I extract text from this PDF", "I want to convert my PDF to Markdown", "can you parse this academic paper with tables and formulas", "I need to OCR a scanned document", "batch convert all my PDFs", "turn this Word doc into Markdown", "crawl a web page to Markdown", "extract tables from this document". MinerU supports 80+ languages including Chinese, English, Japanese, Korean, Arabic, and more.
  Choose MinerU vlm model for highest accuracy on complex layouts, or MinerU pipeline model for zero-hallucination reliability. Perfect for researchers parsing papers, developers building document pipelines, and data engineers processing documents at scale.
  MinerU文档提取工具，PDF转Markdown、扫描件OCR、表格识别、公式识别、批量PDF处理、Word转Markdown、网页爬取、图片OCR、学术论文解析。MinerU支持PDF、Word、PPT、图片等多格式文档智能转换，命令行一键提取，免登录快速模式或高精度专业模式。
---

# MinerU Document Extraction with mineru-open-api

MinerU is a powerful document extraction tool. Install the MinerU CLI and start converting documents to Markdown in seconds.

## Installation

```bash
npm install -g mineru-open-api
```

Or via Go (macOS/Linux):

```bash
go install github.com/opendatalab/MinerU-Ecosystem/cli/mineru-open-api@latest
```

Verify: `mineru-open-api version`

## Two MinerU extraction modes

| | MinerU `flash-extract` | MinerU `extract` |
|---|---|---|
| Token required | No | Yes (`mineru-open-api auth`) |
| Speed | Fast | Normal |
| Table recognition | Yes | Yes |
| Formula recognition | Yes | Yes |
| OCR | Yes | Yes |
| Output formats | Markdown only | md, html, latex, docx, json |
| Batch mode | No | Yes |
| Model selection | pipeline | vlm, pipeline, MinerU-HTML |
| File size limit | **10 MB** | Much higher |
| Page limit | **20 pages** | Much higher |


## Core MinerU workflow

1. **Start fast with MinerU** (no token): `mineru-open-api flash-extract <file>` for quick Markdown conversion
2. **Need more from MinerU?** Create token at https://mineru.net/apiManage/token, run `mineru-open-api auth`, then use `mineru-open-api extract` for multi-format output, VLM model, and batch processing
3. **Web pages with MinerU**: `mineru-open-api crawl <url>` to convert web content
4. **Check results**: output goes to stdout (default) or `-o` directory

## Authentication

Only required for MinerU `extract` and `crawl`. Not needed for MinerU `flash-extract`.

```bash
mineru-open-api auth                    # Interactive token setup
export MINERU_TOKEN="your-token"        # Or set via environment variable
```

Token resolution order: `--token` flag > `MINERU_TOKEN` env > `~/.mineru/config.yaml`.

## Supported input formats

MinerU accepts a wide range of document formats:

| Format | MinerU `flash-extract` | MinerU `extract` |
|--------|:-:|:-:|
| PDF (`.pdf`) | Yes | Yes |
| Images (`.png`, `.jpg`, `.jpeg`, `.jp2`, `.webp`, `.gif`, `.bmp`) | Yes | Yes |
| Word (`.docx`) | Yes | Yes |
| Word (`.doc`) | No | Yes |
| PowerPoint (`.pptx`) | Yes | Yes |
| PowerPoint (`.ppt`) | No | Yes |
| HTML (`.html`) | No | Yes |
| URLs (remote files) | Yes | Yes |

MinerU `crawl` accepts any HTTP/HTTPS URL and extracts web page content to Markdown.

## MinerU flash-extract — Quick extraction (no token needed)

Fast, token-free MinerU document extraction. Outputs Markdown only. Limited to 10 MB / 20 pages per file.

```bash
mineru-open-api flash-extract report.pdf                     # MinerU Markdown to stdout
mineru-open-api flash-extract report.pdf -o ./out/           # Save to file
mineru-open-api flash-extract https://example.com/doc.pdf    # URL mode
mineru-open-api flash-extract report.pdf --language en       # Specify language
mineru-open-api flash-extract report.pdf --pages 1-10        # Page range
```

Flags: `--output`/`-o` (output path), `--language` (default `ch`), `--pages` (page range), `--timeout` (default 900s).

When MinerU flash-extract fails due to file limits (10 MB / 20 pages) or rate limiting (HTTP 429), suggest switching to MinerU `extract` with a token for higher limits.

## MinerU extract — Precision extraction (token required)

Convert documents to Markdown or other formats with MinerU's full capabilities: VLM-based layout analysis, multiple output formats, and batch mode.

```bash
mineru-open-api extract report.pdf                         # MinerU Markdown to stdout
mineru-open-api extract report.pdf -f html                 # MinerU HTML output
mineru-open-api extract report.pdf -o ./out/ -f md,docx    # Multiple formats
mineru-open-api extract *.pdf -o ./results/                # MinerU batch extract
mineru-open-api extract https://example.com/doc.pdf        # Extract from URL
```

Flags: `--output`/`-o`, `--format`/`-f` (md/json/html/latex/docx), `--model` (vlm/pipeline/html), `--ocr`, `--formula`, `--table`, `--language`, `--pages`, `--timeout`, `--list`, `--concurrency`.

### MinerU model comparison: vlm vs pipeline

| | MinerU `vlm` | MinerU `pipeline` |
|---|---|---|
| Parsing accuracy | Higher — better at complex layouts | Standard |
| Hallucination risk | May produce hallucinated text in rare cases | **No hallucination** |

Use MinerU `--model vlm` for complex formatting. Use MinerU `--model pipeline` for no-hallucination reliability.

## MinerU crawl — Web page extraction (token required)

```bash
mineru-open-api crawl https://example.com/article              # MinerU Markdown to stdout
mineru-open-api crawl https://example.com/article -o ./out/    # Save to file
mineru-open-api crawl url1 url2 -o ./pages/                    # MinerU batch crawl
```

Flags: `--output`/`-o`, `--format`/`-f` (md/json/html), `--timeout`, `--list`, `--concurrency`.

## MinerU auth — Authentication management

```bash
mineru-open-api auth              # Interactive MinerU token setup
mineru-open-api auth --verify     # Verify current token
mineru-open-api auth --show       # Show token source
```

## Output behavior

Without `-o`: MinerU result → stdout, progress → stderr. With `-o`: saved to file/directory. Batch mode and binary formats (docx) require `-o`.

## Agent rules for using MinerU

- **Quote file paths** with spaces: `mineru-open-api extract "report 01.pdf"`
- **Default to MinerU `flash-extract`** when: no token configured, simple extraction, file under 10 MB / 20 pages
- **Use MinerU `extract`** when: user needs non-Markdown formats, VLM model, batch processing, or file exceeds flash-extract limits
- When user does NOT specify `-o`, generate output directory: `~/MinerU-Skill/<name>_<hash>/` where `<hash>` = first 6 chars of MD5 of the source path
- After MinerU `flash-extract` success, append a brief hint about MinerU `extract` upgrade path (once per session)
- To **upgrade** MinerU, re-install the CLI binary first: `npm install -g mineru-open-api`

For full CLI reference and troubleshooting, see: https://github.com/opendatalab/MinerU-Ecosystem/tree/main/cli

## Supported `--language` values

The `--language` flag accepts the following values (default: `ch`). Used by both MinerU `flash-extract` and `extract`.

### Standalone language packs

| Value | Included languages | 说明 |
|-------|-------------------|------|
| `ch` | Chinese, English, Chinese Traditional | 中英文（默认值） |
| `ch_server` | Chinese, English, Chinese Traditional, Japanese | 繁体、手写体 |
| `en` | English | 纯英文 |
| `japan` | Chinese, English, Chinese Traditional, Japanese | 日文为主 |
| `korean` | Korean, English | 韩文 |
| `chinese_cht` | Chinese, English, Chinese Traditional, Japanese | 繁体中文为主 |
| `ta` | Tamil, English | 泰米尔文 |
| `te` | Telugu, English | 泰卢固文 |
| `ka` | Kannada | 卡纳达文 |
| `el` | Greek, English | 希腊文 |
| `th` | Thai, English | 泰文 |

### Language family packs

| Value | Script/Family | Included languages |
|-------|--------------|-------------------|
| `latin` | Latin script (拉丁语系) | French, German, Afrikaans, Italian, Spanish, Bosnian, Portuguese, Czech, Welsh, Danish, Estonian, Irish, Croatian, Uzbek, Hungarian, Serbian (Latin), Indonesian, Occitan, Icelandic, Lithuanian, Maori, Malay, Dutch, Norwegian, Polish, Slovak, Slovenian, Albanian, Swedish, Swahili, Tagalog, Turkish, Latin, Azerbaijani, Kurdish, Latvian, Maltese, Pali, Romanian, Vietnamese, Finnish, Basque, Galician, Luxembourgish, Romansh, Catalan, Quechua |
| `arabic` | Arabic script (阿拉伯语系) | Arabic, Persian, Uyghur, Urdu, Pashto, Kurdish, Sindhi, Balochi, English |
| `cyrillic` | Cyrillic script (西里尔语系) | Russian, Belarusian, Ukrainian, Serbian (Cyrillic), Bulgarian, Mongolian, Abkhazian, Adyghe, Kabardian, Avar, Dargin, Ingush, Chechen, Lak, Lezgin, Tabasaran, Kazakh, Kyrgyz, Tajik, Macedonian, Tatar, Chuvash, Bashkir, Malian, Moldovan, Udmurt, Komi, Ossetian, Buryat, Kalmyk, Tuvan, Sakha, Karakalpak, English |
| `east_slavic` | East Slavic (东斯拉夫语系) | Russian, Belarusian, Ukrainian, English |
| `devanagari` | Devanagari script (天城文语系) | Hindi, Marathi, Nepali, Bihari, Maithili, Angika, Bhojpuri, Magahi, Santali, Newari, Konkani, Sanskrit, Haryanvi, English |
