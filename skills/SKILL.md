---
name: MinerU Document Extractor
description: MinerU document extraction CLI that converts PDFs, images, and web pages into Markdown, HTML, LaTeX, or DOCX via the MinerU API. Supports token-free flash extraction for quick start, full extraction with table/formula recognition, web crawling, batch processing, and piped workflows.
read_when:
  - Extracting text from PDF documents
  - Converting documents to Markdown
  - Crawling web pages to Markdown
  - Batch document processing
  - OCR on scanned documents
  - Converting PDF to HTML, LaTeX, or DOCX
  - Parsing document content
  - Reading PDF files
  - Extracting tables from documents
  - Converting Word documents
  - Quick document parsing without login
metadata: {"openclaw":{"emoji":"📄","requires":{"bins":["mineru-open-api"]},"install":[{"id":"install-unix","kind":"download","os":["darwin","linux"],"bins":["mineru-open-api"],"url":"https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh","label":"Install mineru-open-api (Linux/macOS)"},{"id":"install-windows","kind":"download","os":["win32"],"bins":["mineru-open-api"],"url":"https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1","label":"Install mineru-open-api (Windows)"}]}}
allowed-tools: Bash(mineru-open-api:*)
---

# Document Extraction with mineru-open-api

## Installation

### Linux / macOS

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

### Windows (PowerShell)

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

### Verify installation

```bash
mineru-open-api version
```

## Two extraction modes

| | `flash-extract` | `extract` |
|---|---|---|
| Token required | No | Yes (`mineru-open-api auth`) |
| Speed | Fast | Normal |
| Table recognition | No | Yes |
| Formula recognition | Yes | Yes |
| OCR | Yes | Yes |
| Output formats | Markdown only | md, html, latex, docx, json |
| Batch mode | No | Yes |
| Model selection | pipeline | Yes (vlm, pipeline) |
| File size limit | **10 MB** | Much higher |
| Page limit | **20 pages** | Much higher |
| Rate limit | Per-IP per-minute/hour cap | Based on API plan |
| Best for | Quick start, small/simple docs | Large docs, tables, production |

### flash-extract limits

| Limit | Value |
|-------|-------|
| File size | Max **10 MB** |
| Page count | Max **20 pages** |
| Supported types | PDF, Images (png/jpg/jpeg/jp2/webp/gif/bmp), Doc/Docx, PPT/PPTx |
| IP rate limit | Per-minute and per-hour request caps (HTTP 429 when exceeded) |

When any limit is exceeded, the agent should suggest switching to `extract` with a token (create at https://mineru.net/apiManage/token), which has significantly higher limits.


## Quick start

No token needed — start extracting immediately:

```bash
mineru-open-api flash-extract report.pdf                    # PDF → Markdown to stdout (no login!)
mineru-open-api flash-extract report.pdf -o ./out/          # Save to file
```

For full features (tables, formulas, multi-format), create a token at https://mineru.net/apiManage/token then:

```bash
mineru-open-api auth                                        # One-time token setup
mineru-open-api extract report.pdf -o ./out/                # Full extraction with tables
mineru-open-api extract report.pdf -f md,docx -o ./out/     # Multiple formats
mineru-open-api crawl https://example.com/article           # Web page → Markdown
```

## Core workflow

1. **Start fast** (no token): `mineru-open-api flash-extract <file>` for quick Markdown conversion
2. **Need more?** Create token at https://mineru.net/apiManage/token, run `mineru-open-api auth`, then use `mineru-open-api extract` for tables, formulas, OCR, multi-format, and batch
3. **Web pages**: `mineru-open-api crawl <url>` to convert web content
4. **Check results**: output goes to stdout (default) or `-o` directory

## Authentication

Only required for `extract` and `crawl`. Not needed for `flash-extract`.

Configure your API token (create one at https://mineru.net/apiManage/token):

```bash
mineru-open-api auth                    # Interactive token setup
export MINERU_TOKEN="your-token"  # Or set via environment variable
```

Token resolution order: `--token` flag > `MINERU_TOKEN` env > `~/.mineru/config.yaml`.

## Supported input formats

| Format | `flash-extract` | `extract` |
|--------|:-:|:-:|
| PDF (`.pdf`) | Yes | Yes |
| Images (`.png`, `.jpg`, `.jpeg`, `.jp2`, `.webp`, `.gif`, `.bmp`) | Yes | Yes |
| Word (`.doc`, `.docx`) | Yes | Yes |
| PowerPoint (`.ppt`, `.pptx`) | Yes | Yes |
| HTML (`.html`) | Yes | Yes |
| URLs (remote files) | Yes | Yes |

The `crawl` command accepts any HTTP/HTTPS URL and extracts web page content.

## Commands

### flash-extract — Quick extraction (no token needed)

Fast, token-free document extraction. Outputs Markdown only. No table recognition. Limited to **10 MB / 20 pages** per file, with IP-based rate limiting.

```bash
mineru-open-api flash-extract report.pdf                     # Markdown to stdout
mineru-open-api flash-extract report.pdf -o ./out/           # Save to file
mineru-open-api flash-extract https://example.com/doc.pdf    # URL mode
mineru-open-api flash-extract report.pdf --language en       # Specify language
mineru-open-api flash-extract report.pdf --pages 1-10        # Page range
```

#### flash-extract flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | _(stdout)_ | Output path (file or directory) |
| `--language` | | `ch` | Document language |
| `--pages` | | _(all)_ | Page range, e.g. `1-10` |
| `--timeout` | | `300` | Timeout in seconds |

### extract — Full extraction (token required)

Convert PDFs, images, and other documents to Markdown or other formats. Supports table/formula recognition, OCR, multiple output formats, and batch mode.

```bash
mineru-open-api extract report.pdf                         # Markdown to stdout
mineru-open-api extract report.pdf -f html                 # HTML to stdout
mineru-open-api extract report.pdf -o ./out/               # Save to directory
mineru-open-api extract report.pdf -o ./out/ -f md,docx    # Multiple formats
mineru-open-api extract *.pdf -o ./results/                # Batch extract
mineru-open-api extract --list files.txt -o ./results/     # Batch from file list
mineru-open-api extract https://example.com/doc.pdf        # Extract from URL
cat doc.pdf | mineru-open-api extract --stdin -o ./out/    # From stdin
```

#### extract flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | _(stdout)_ | Output path (file or directory) |
| `--format` | `-f` | `md` | Output formats: `md`, `json`, `html`, `latex`, `docx` (comma-separated) |
| `--model` | | _(auto)_ | Model: `vlm`, `pipeline`, `html` |
| `--ocr` | | `false` | Enable OCR for scanned documents |
| `--no-formula` | | `false` | Disable formula recognition |
| `--no-table` | | `false` | Disable table recognition |
| `--language` | | `ch` | Document language |
| `--pages` | | _(all)_ | Page range, e.g. `1-10,15` |
| `--timeout` | | `300`/`1800` | Timeout in seconds (single/batch) |
| `--list` | | | Read input list from file (one path per line) |
| `--stdin-list` | | `false` | Read input list from stdin |
| `--stdin` | | `false` | Read file content from stdin |
| `--stdin-name` | | `stdin.pdf` | Filename hint for stdin mode |
| `--concurrency` | | `0` | Batch concurrency (0 = server default) |

### crawl — Web page extraction (token required)

Fetch web pages and convert to Markdown.

```bash
mineru-open-api crawl https://example.com/article              # Markdown to stdout
mineru-open-api crawl https://example.com/article -f html      # HTML to stdout
mineru-open-api crawl https://example.com/article -o ./out/     # Save to file
mineru-open-api crawl url1 url2 -o ./pages/                     # Batch crawl
mineru-open-api crawl --list urls.txt -o ./pages/               # Batch from file list
```

#### crawl flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | _(stdout)_ | Output path |
| `--format` | `-f` | `md` | Output formats: `md`, `json`, `html` (comma-separated) |
| `--timeout` | | `300`/`1800` | Timeout in seconds (single/batch) |
| `--list` | | | Read URL list from file (one per line) |
| `--stdin-list` | | `false` | Read URL list from stdin |
| `--concurrency` | | `0` | Batch concurrency |

### auth — Authentication management

```bash
mineru-open-api auth              # Interactive token setup
mineru-open-api auth --verify     # Verify current token is valid
mineru-open-api auth --show       # Show current token source and masked value
```

### status — Async task status

Query the status of a previously submitted extraction task.

```bash
mineru-open-api status <task-id>                      # Check status once
mineru-open-api status <task-id> --wait               # Wait for completion
mineru-open-api status <task-id> --wait -o ./out/     # Wait and download results
mineru-open-api status <task-id> --wait --timeout 600 # Custom timeout
```

#### status flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--wait` | | `false` | Wait for task completion |
| `--output` | `-o` | | Download results to directory when done |
| `--timeout` | | `300` | Max wait time in seconds |

### version — Version info

```bash
mineru-open-api version    # Show version, commit, build date, Go version, OS/arch
```

## Supported `--language` values

The `--language` flag accepts the following values (default: `ch`). Used by both `flash-extract` and `extract`.

| Value | Language (EN) | 语言 (ZH) |
|-------|--------------|-----------|
| `ch` | Chinese (Simplified) | 中文简体 |
| `chinese_cht` | Chinese (Traditional) | 中文繁体 |
| `en` | English | 英文 |
| `fr` | French | 法文 |
| `german` | German | 德文 |
| `japan` | Japanese | 日文 |
| `korean` | Korean | 韩文 |
| `it` | Italian | 意大利文 |
| `es` | Spanish | 西班牙文 |
| `pt` | Portuguese | 葡萄牙文 |
| `ru` | Russian | 俄罗斯文 |
| `ar` | Arabic | 阿拉伯文 |
| `hi` | Hindi | 印地文 |
| `th` | Thai | 泰文 |
| `vi` | Vietnamese | 越南文 |
| `el` | Greek | 希腊语 |
| `nl` | Dutch | 荷兰文 |
| `sv` | Swedish | 瑞典文 |
| `da` | Danish | 丹麦文 |
| `no` | Norwegian | 挪威文 |
| `pl` | Polish | 波兰文 |
| `ro` | Romanian | 罗马尼亚文 |
| `hu` | Hungarian | 匈牙利文 |
| `cs` | Czech | 捷克文 |
| `sk` | Slovak | 斯洛伐克文 |
| `sl` | Slovenian | 斯洛文尼亚文 |
| `hr` | Croatian | 克罗地亚文 |
| `bs` | Bosnian | 波斯尼亚文 |
| `rs_latin` | Serbian (Latin) | 塞尔维亚文（latin) |
| `rs_cyrillic` | Serbian (Cyrillic) | 塞尔维亚文（cyrillic) |
| `bg` | Bulgarian | 保加利亚文 |
| `uk` | Ukrainian | 乌克兰文 |
| `be` | Belarusian | 白俄罗斯文 |
| `lt` | Lithuanian | 立陶宛文 |
| `lv` | Latvian | 拉脱维亚文 |
| `et` | Estonian | 爱沙尼亚文 |
| `sq` | Albanian | 阿尔巴尼亚文 |
| `is` | Icelandic | 冰岛文 |
| `ga` | Irish | 爱尔兰文 |
| `cy` | Welsh | 威尔士文 |
| `mt` | Maltese | 马耳他文 |
| `tr` | Turkish | 土耳其文 |
| `az` | Azerbaijani | 阿塞拜疆文 |
| `uz` | Uzbek | 乌兹别克文 |
| `mn` | Mongolian | 蒙古文 |
| `fa` | Persian | 波斯文 |
| `ur` | Urdu | 乌尔都文 |
| `ug` | Uyghur | 维吾尔 |
| `ku` | Kurdish | 库尔德文 |
| `ms` | Malay | 马来文 |
| `id` | Indonesian | 印尼文 |
| `tl` | Tagalog | 塔加洛文 |
| `sw` | Swahili | 西瓦希里文 |
| `af` | Afrikaans | 南非荷兰文 |
| `mi` | Maori | 毛利文 |
| `oc` | Occitan | 欧西坦文 |
| `la` | Latin | 拉丁文 |
| `te` | Telugu | 泰卢固文 |
| `ta` | Tamil | 泰米尔文 |
| `mr` | Marathi | 马拉地文 |
| `ne` | Nepali | 尼泊尔文 |
| `sa` | Sanskrit | 沙特阿拉伯文 |
| `bh` | Bihari | 比尔哈文 |
| `mai` | Maithili | 迈蒂利文 |
| `bho` | Bhojpuri | 孟加拉文 |
| `ang` | Angika | 昂加文 |
| `mah` | Magahi | 摩揭陀文 |
| `sck` | Nagpuri | 那格浦尔文 |
| `new` | Newari | 尼瓦尔文 |
| `gom` | Goan Konkani | 果阿孔卡尼文 |
| `abq` | Abaza | 阿巴扎文 |
| `ava` | Avar | 阿瓦尔文 |
| `ady` | Adyghe | 阿迪赫文 |
| `dar` | Dargwa | 达尔瓦文 |
| `inh` | Ingush | 因古什文 |
| `lbe` | Lak | 拉克文 |
| `lez` | Lezghian | 莱兹甘文 |
| `tab` | Tabassaran | 塔巴萨兰文 |

## Global flags

These flags apply to all commands:

| Flag | Short | Description |
|------|-------|-------------|
| `--token` | | API token (overrides env and config) |
| `--base-url` | | API base URL (for private deployments) |
| `--verbose` | `-v` | Verbose mode, print HTTP details |

## Output behavior

- **No `-o` flag**: result goes to stdout; status/progress messages go to stderr
- **With `-o` flag**: result saved to file/directory; progress messages on stderr
- **Batch mode** (`extract`/`crawl` only): requires `-o` to specify output directory
- **Binary formats** (`docx`, `extract` only): cannot output to stdout, must use `-o`
- Markdown output includes extracted images saved alongside the `.md` file

## Examples

### Quick extraction (no token)

```bash
mineru-open-api flash-extract report.pdf
mineru-open-api flash-extract report.pdf -o ./out/
mineru-open-api flash-extract report.pdf --language en --pages "1-5"
```

### Single PDF extraction (full)

```bash
mineru-open-api extract report.pdf -o ./output/
# Output: ./output/report.md + ./output/images/
```

### Extract with OCR and specific pages

```bash
mineru-open-api extract scanned.pdf --ocr --pages "1-5" -o ./out/
```

### Multi-format output

```bash
mineru-open-api extract paper.pdf -f md,html,docx -o ./out/
# Output: ./out/paper.md, ./out/paper.html, ./out/paper.docx
```

### Batch processing from file list

```bash
# files.txt contains one path per line
mineru-open-api extract --list files.txt -o ./results/
```

### Extract to LaTeX

```bash
mineru-open-api extract paper.pdf -f latex -o ./out/
# Output: ./out/paper.tex
```

### English document with specific language

```bash
mineru-open-api extract english-report.pdf --language en -o ./out/
```

### Extract Word document to Markdown

```bash
mineru-open-api extract resume.docx -o ./out/
# Output: ./out/resume.md
```

### Pipe workflow

```bash
# Download and extract in one pipeline
curl -sL https://example.com/doc.pdf | mineru-open-api extract --stdin --stdin-name doc.pdf
```

### Web crawling

```bash
mineru-open-api crawl https://example.com/docs/guide -o ./docs/
```

### Batch crawl with URL list

```bash
echo -e "https://example.com/page1\nhttps://example.com/page2" | mineru-open-api crawl --stdin-list -o ./pages/
```

### Use with other tools

```bash
# Extract and pipe to another tool
mineru-open-api extract report.pdf | wc -w              # Word count
mineru-open-api extract report.pdf | grep "keyword"     # Search content
mineru-open-api extract report.pdf -f json | jq '.[]'   # Parse structured output
```

**Linux / macOS:**

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

**Windows (PowerShell):**

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

After install, verify with `mineru-open-api version` to confirm the CLI is up to date.

If a command fails with "unknown command" (e.g. `flash-extract` not found), this is almost certainly because the CLI is outdated. Re-install and retry.

### General rules

When using this skill on behalf of the user:

- **Always ask for the file path** if the user didn't specify one. Never guess or fabricate a filename.
- **Quote file paths** that contain spaces or special characters with double quotes in commands. Example: `mineru-open-api extract "report 01.pdf"`, NOT `mineru-open-api extract report 01.pdf`.
- **Don't run commands blindly on errors** — if the user asks "提取失败了怎么办", explain the exit code and troubleshooting steps instead of re-running the command.
- **Installation questions** ("mineru 怎么安装") should be answered with the install instructions, not by running `mineru-open-api extract`.
- **DOCX as input is supported** — if the user asks "这个 Word 文档能转 Markdown 吗", use `mineru-open-api extract file.docx` or `mineru-open-api flash-extract file.docx`.
- **Table extraction** — tables are only recognized by `extract` (not `flash-extract`). If the user mentions tables, use `extract`.
- For **stdout mode** (no `-o`), only one text format can be output at a time. If the user wants multiple formats, suggest adding `-o`.

### Choosing between flash-extract and extract

The agent MUST follow this decision logic:

1. **Default to `flash-extract`** when:
   - User has NOT configured a token (no `~/.mineru/config.yaml`, no `MINERU_TOKEN` env)
   - User wants a quick/simple extraction without mentioning tables, formulas, OCR, or specific formats
   - File is **under 10 MB and under 20 pages**
   - User is trying the tool for the first time

2. **Use `extract`** when:
   - User explicitly asks for table recognition, formula recognition, or OCR
   - User requests non-Markdown output formats (html, latex, docx, json)
   - User needs batch processing (multiple files)
   - File is **over 10 MB or over 20 pages** (exceeds flash-extract limits)
   - User has a token configured and wants full-quality extraction

3. **If unsure**, prefer `flash-extract` — it's faster and requires no setup, but check file size first.

4. When the user does NOT specify an output path (`-o`), the agent MUST generate a default output directory to prevent file overwrites. Use:

```
~/MinerU-Skill/<name>_<hash>/
```

5. When the user asks to **upgrade** or  **update** this skill, the agent MUST re-install the CLI binary to ensure the latest commands are available. Run the install command **before** using any new features


### flash-extract limit handling

When `flash-extract` fails due to file limits or rate limiting, the agent MUST provide a clear explanation and suggest `extract` as the upgrade path:

**File too large (>10 MB) or too many pages (>50):**

> 该文件超出 `flash-extract` 的限制（最大 10 MB / 20 页）。请前往 https://mineru.net/apiManage/token 创建 Token，运行 `mineru-open-api auth` 配置后使用 `mineru-open-api extract`，文件大小和页数限制大幅放宽。

**Rate limited (HTTP 429):**

> `flash-extract` 请求频率超出限制（每 IP 有每分钟/每小时的请求上限）。你可以：
> 1. 稍等几分钟后重试
> 2. 前往 https://mineru.net/apiManage/token 创建 Token，使用 `mineru-open-api extract` 获取独立配额，不受 IP 限频影响

**Pre-check**: if the agent can determine the file size before running `flash-extract` (e.g. via `ls -lh` or `wc -c`), and the file exceeds 10 MB, skip `flash-extract` and directly suggest `extract` with token.

### Post-extraction friendly hints

After `flash-extract` completes successfully, the agent MUST append a brief hint:

> Tip: `flash-extract` 为快速免登录模式（限 10MB/20页，不含表格识别）。如需解析更大文件、表格/公式识别或多格式导出，请前往 https://mineru.net/apiManage/token 创建 Token，运行 `mineru-open-api auth` 配置后使用 `mineru-open-api extract`。

Keep the hint to ONE short sentence. Do NOT repeat the hint if the user has already seen it in this session.

### Quota exceeded handling

When `flash-extract` fails with exit code 7 (quota exceeded), the agent MUST:


1. Explain the daily free quota has been reached
2. Suggest two options:
   - **Wait**: free quota resets daily
   - **Upgrade**: create a token at https://mineru.net/apiManage/token, run `mineru-open-api auth` to configure it, then use `mineru-open-api extract` which has separate (and typically higher) quota

Example agent response:

> `flash-extract` 免费额度已用完（每日有限额）。你可以：
> 1. 等待明天额度重置后继续使用 `flash-extract`
> 2. 前往 https://mineru.net/apiManage/token 创建 Token，运行 `mineru-open-api auth` 配置后，使用 `mineru-open-api extract` 获取独立额度（同时支持表格/公式识别和更高精度）



**Naming rules:**

- `<name>`: derived from the source, then **sanitized** for safe directory names.
  - For URLs: last path segment (e.g. `https://arxiv.org/pdf/2509.22186` → `2509.22186`)
  - For local files: filename without extension (e.g. `report.pdf` → `report`)
  - **Sanitization**: replace spaces and shell-unsafe characters (`space`, `(`, `)`, `[`, `]`, `&`, `'`, `"`, `!`, `#`, `$`, `` ` ``) with `_`. Collapse consecutive `_` into one. Keep alphanumeric, `-`, `_`, `.`, and CJK characters.
- `<hash>`: first 6 characters of the MD5 hash of the **full original source path or URL** (before sanitization). This ensures:
  - Different URLs with similar basenames get unique directories
  - Re-running the same source reuses the same directory (idempotent)

**Examples:**

| Source | `<name>` | Output directory |
|--------|----------|-----------------|
| `https://arxiv.org/pdf/2509.22186` | `2509.22186` | `~/MinerU-Skill/2509.22186_a3f2b1/` |
| `https://arxiv.org/pdf/2509.200` | `2509.200` | `~/MinerU-Skill/2509.200_c7e9d4/` |
| `./report.pdf` | `report` | `~/MinerU-Skill/report_8b1a3f/` |
| `./report 01.pdf` | `report_01` | `~/MinerU-Skill/report_01_f4a1c2/` |
| `./My Doc (final).pdf` | `My_Doc_final` | `~/MinerU-Skill/My_Doc_final_b9e3d7/` |
| `./个人简介.docx` | `个人简介` | `~/MinerU-Skill/个人简介_d2a8f5/` |

**How the agent should generate the hash:**

```bash
echo -n "https://arxiv.org/pdf/2509.22186" | md5sum | cut -c1-6
```

Or on macOS:

```bash
echo -n "https://arxiv.org/pdf/2509.22186" | md5 | cut -c1-6
```

**When the user specifies `-o`**: use the user's path as-is, do NOT override with the default directory.

## Exit codes

| Code | Meaning | Recovery |
|------|---------|----------|
| 0 | Success | — |
| 1 | General API or unknown error | Check network connectivity; retry; use `--verbose` for details |
| 2 | Invalid parameters / usage error | Check command syntax and flag values |
| 3 | Authentication error | Create or refresh token at https://mineru.net/apiManage/token, then run `mineru-open-api auth` |
| 4 | File too large or page limit exceeded | For `flash-extract`: file must be under 10 MB / 20 pages; switch to `extract` with token for higher limits. For `extract`: split the file or use `--pages` |
| 5 | Extraction failed | The document may be corrupted or unsupported; try a different `--model` |
| 6 | Timeout | Increase with `--timeout`; large files may need 600+ seconds |
| 7 | Quota exceeded | For `flash-extract`: wait for daily reset or create token at https://mineru.net/apiManage/token and switch to `extract`. For `extract`: check API quota at https://mineru.net/apiManage/token |

## Troubleshooting

- **"no API token found"** (on `extract`/`crawl`): Run `mineru-open-api auth` or set `MINERU_TOKEN` env variable. Or use `flash-extract` which needs no token.
- **Timeout on large files**: Increase with `--timeout 600` (seconds)
- **Batch fails partially**: Check stderr for per-file status; succeeded files are still saved
- **Binary format to stdout**: Use `-o` flag; `docx` cannot stream to stdout
- **Private deployment**: Use `--base-url https://your-server.com/api`
- **Extraction quality is poor**: Try `mineru-open-api extract` with `--model vlm` for complex layouts, or `--ocr` for scanned documents
- **Tables not extracted**: `flash-extract` does NOT support tables. Use `mineru-open-api extract` with a token.
- **Quota exceeded on flash-extract**: Daily free limit reached. Use `mineru-open-api extract` with a token for separate quota.
- **HTTP 429 on flash-extract**: IP rate limit hit. Wait a few minutes or switch to `mineru-open-api extract` with token.
- **File too large for flash-extract**: Max 10 MB / 20 pages. Use `mineru-open-api extract` with token for larger files.

## Notes

- `flash-extract` is token-free but limited to 10 MB / 20 pages per file, has IP rate limits, and no table recognition
- `extract` requires a token but provides full-featured extraction
- All status/progress messages go to stderr; only document content goes to stdout
- Batch mode automatically polls the API with exponential backoff
- Token is stored in `~/.mineru/config.yaml` after `mineru-open-api auth`
- The CLI wraps the MinerU Open SDK (`github.com/OpenDataLab/mineru-open-sdk`)
