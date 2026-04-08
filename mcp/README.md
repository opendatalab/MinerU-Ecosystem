# MinerU Open MCP

An Official Mineru  MCP server that exposes [MinerU](https://mineru.net)'s document parsing as MCP tools. Connect any MCP-compatible AI client to convert PDFs, Word docs, PowerPoint files, and images into Markdown, Word (docx), HTML, or LaTeX.

**No API key required** — Flash mode works out of the box, free with no sign-up, for files up to 20 pages / 10 MB. Set `MINERU_API_TOKEN` to unlock higher limits and extra output formats.

---

## ⚡ Quickest Way to Run — uvx (no install needed)

`mineru-open-mcp` is on PyPI. With `uv` installed, you can run it directly — no separate install step.

### Configure your MCP client

#### stdio — Claude Desktop, Cursor, Windsurf

The MCP client launches `mineru-open-mcp` as a subprocess automatically.

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


> **No API key?** The server runs in Flash mode — free, markdown-only, 20 pages / 10 MB per file (PDF, images, Docx, PPTx, xls, xlsx).

> **`mineru-open-mcp` not on PATH?** Use the full path: `"/Users/you/.local/bin/mineru-open-mcp"`, or use the `uvx` approach above which handles this automatically.

## Usage Examples

### Example 1: Parse a local PDF document with target page ranges
**User prompt:** "Parse the 3rd-5th pages of this PDF into markdown: \<your_path_to_file\>"
**What happens:**
- MinerU uploads and parses the PDF
- Returns clean Markdown (if you configured MINERU_API_TOKEN, you can also
prompt word, html, latex as the output) with tables (HTML) and formulas (Latex) preserved
- Returns markdown texts in the chat if length permitted along with the output path, and the zip url if you prefer
- Claude summarizes the content

### Example 2: Parse a remote url hosting a file
**User prompt:** "Extract contents from this paper: https://arxiv.org/pdf/2509.22186"
**What happens:**
- MinerU parses the paper into markdown
- Claude formats and explains the tables

### Example 3:  Parse local PDF files with independent page ranges 
**User prompt:** "Parse \<file1\> page 1-5, \<file2\> page 2-9, \<file3\> page 3 into markdown/word "
**What happens:**
- MinerU uploads and parses the files separatedly
- Returns target format ouputs, the zip url for you to download, markdown abstract, the directory you 
want to save the output to
- Claude uses the content for further analysis

### Example 4: Advanced custom preferences
**User prompt1:** "use pipeline model to parse this Korean file your_path_here"
**User prompt2:** "parse your_path_here and save the markdown to your_output_dir"
**What happends:**
- Pipeline model is another model provided by MinerU service (BTW, vlm model is the default choice)
- You are allowed to specify a model, an ocr language, or even an independent output dir 
different from OUTPUT_DIR by structuring your prompt
- Your requests are parameterized into parse_documents tool and MinerU will handle the rest. 



#### streamable-http — web-based MCP clients

Start the server manually, then point your client at it:

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

## Features

- **`parse_documents`** ? convert local files and/or remote URLs to Markdown; Input supports PDF, images（png/jpg/jpeg/jp2/webp/gif/bmp, Doc, Docx, Ppt, PPTx. Flash Mode also supports xlsx.
- **`get_ocr_languages`** — list all OCR languages supported by MinerU
- **Flash mode** — works without an API key (free, markdown output only, 20 pages / 10 MB per file, supports PDF/images/Docx/PPTx/xls/xlsx); For full features, please provide `MINERU_API_TOKEN`, which will disable flash mode.
- **Output behavior** ? single-file parses return inline Markdown by default; batch parses save results to disk and return file metadata. Oversized inline content is also saved locally and returned via `extract_path`.
- **Two transport modes** ? `stdio`, `streamable-http`


---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU API token, apply on [MinerU](https://mineru.net) for full capability. If not provided, flash mode is enabled. | — |
| `OUTPUT_DIR` | Directory used when parsed results need to be saved locally, such as batch parsing or oversized inline content | `~/mineru-downloads` |




## Privacy Policy

`mineru-open-mcp` connects to the official MinerU API (mineru.net) to parse documents.

- **Data sent**: Document content (files or URLs you provide for parsing)
- **Data storage**: Parsed results are temporarily cached by MinerU servers; not used for training
- **Third-party**: MinerU API (mineru.net) — see [MinerU Privacy Policy](https://mineru.net/privacyPolicy)
- **Local data**: Parsed results will be saved to target output directory. Log files (only when ENABLE_LOG=true), saved to MINERU_LOG_DIR;
- **Contact**: OpenDataLab@pjlab.org.cn (or raise an issue at [MinerU-Ecosystem](https://github.com/opendatalab/MinerU-Ecosystem) )