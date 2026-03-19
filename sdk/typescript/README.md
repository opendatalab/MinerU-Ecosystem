# MinerU Open API SDK (JS/TS)

[![npm version](https://badge.fury.io/js/mineru-open-sdk.svg)](https://badge.fury.io/js/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free TypeScript/JavaScript library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one line of code.

The published package targets Node.js 18+. Bun and Deno can also work when Node-compatible APIs are available. Browser use is not a first-class target today; see [Environment Limits](#-environment-limits).

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Flash Mode (No Auth)**: Extract text instantly without an API token.
- **Full Feature Mode**: Comprehensive extraction with layout preservation, images, and formula support.
- **Blocking And Async Primitives**: Use `extract()` for simple flows, or `submit()` / `getTask()` / `getBatch()` for your own polling logic.
- **Built-in Save Helpers**: Save Markdown, HTML, LaTeX, DOCX, or the full extracted zip with exported helpers.

---

## 📦 Install

```bash
npm install mineru-open-sdk
```

---

## 🛠️ Quick Start

### 1. Flash Extract (Fast, No Auth, Markdown-only)
Ideal for quick previews. No token required.

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU();
const result = await client.flashExtract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
);

console.log(result.markdown);
```

### 2. Full Feature Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU("your-api-token");
const result = await client.extract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
);

console.log(result.markdown);
console.log(result.images);
```

---

## 🧩 Supported Public API

### Client lifecycle

- `new MinerU(token?: string, baseUrl = "https://mineru.net/api/v4", flashBaseUrl?: string)`
- `client.setSource("your-app")`

### Blocking extraction methods

- `client.extract(source, options?) -> Promise<ExtractResult>`
- `client.extractBatch(sources, options?) -> AsyncGenerator<ExtractResult>`
- `client.crawl(url, options?) -> Promise<ExtractResult>`
- `client.crawlBatch(urls, options?) -> AsyncGenerator<ExtractResult>`
- `client.flashExtract(source, options?) -> Promise<ExtractResult>`

### Submit/query methods

- `client.submit(source, options?) -> Promise<string>`
- `client.submitBatch(sources, options?) -> Promise<string>`
- `client.getTask(taskId) -> Promise<ExtractResult>`
- `client.getBatch(batchId) -> Promise<ExtractResult[]>`

### Result and save helpers

- `saveMarkdown(result, path, withImages = true)`
- `saveDocx(result, path)`
- `saveHtml(result, path)`
- `saveLatex(result, path)`
- `saveAll(result, dir)`
- `progressPercent(progress)`
- `progressToString(progress)`

### Result fields you will usually use

- `result.taskId`
- `result.state`
- `result.progress`
- `result.markdown`
- `result.images`
- `result.contentList`
- `result.docx`
- `result.html`
- `result.latex`
- `result.filename`
- `result.error`

---

## 📊 Mode Comparison

| Feature | Flash Extract | Full Feature Extract |
| :--- | :--- | :--- |
| **Auth** | **No Auth Required** | **Auth Required (Token)** |
| **Speed** | Blazing Fast | Standard |
| **File Limit** | Max 10 MB | Max 200 MB |
| **Page Limit** | Max 20 Pages | Max 600 Pages |
| **Formats** | PDF, Images, Docx, PPTx, Excel | PDF, Images, Doc/x, Ppt/x, Html |
| **Content** | Markdown only (Placeholders) | Full assets (Images, Tables, Formulas) |
| **Output** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ Defaults And Option Behavior

### `new MinerU(...)`

| Argument | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `token` | `undefined` | Reads `process.env.MINERU_TOKEN` when available |
| `baseUrl` | `https://mineru.net/api/v4` | Standard API base URL |
| `flashBaseUrl` | SDK internal flash URL | Override flash API endpoint for testing/private deployments |

If neither `token` nor `process.env.MINERU_TOKEN` is available, the client works in **flash-only mode**: `flashExtract()` works, while auth-required methods throw `NoAuthClientError`.

### Full-feature methods

These defaults apply to `extract()`, `submit()`, `extractBatch()`, and `submitBatch()` unless noted otherwise.

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `model` | `undefined` | Auto-infers model from the source: `.html` / `.htm` becomes `"html"` (`"MinerU-HTML"` at the API layer), everything else uses `"vlm"` |
| `ocr` | `undefined` | OCR is disabled (API default) |
| `formula` | `undefined` | Formula recognition is enabled (API default) |
| `table` | `undefined` | Table recognition is enabled (API default) |
| `language` | `undefined` | Chinese `"ch"` (API default) |
| `pages` | `undefined` | Full document is processed. Only available on single-source `extract()` / `submit()` |
| `extraFormats` | `undefined` | Only the default Markdown/JSON payload is returned |
| `fileParams` | `undefined` | Per-file overrides for batch methods. Keys are paths/URLs, values are `{ pages?, ocr?, dataId? }` |
| `timeout` | `300` seconds | Max total polling time for `extract()` / `crawl()` |
| `timeout` | `1800` seconds | Max total polling time for `extractBatch()` / `crawlBatch()` |

### `crawl()` / `crawlBatch()`

- `crawl()` is shorthand for `extract(url, { model: "html", ... })`
- `crawlBatch()` is shorthand for `extractBatch(urls, { model: "html", ... })`
- `crawl()` / `crawlBatch()` only expose `extraFormats` and `timeout`, not OCR/table/formula switches

### Flash mode

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `language` | `"ch"` | Chinese is the default |
| `pageRange` | `undefined` | Full page range allowed by the flash API |
| `timeout` | `300` seconds | Max total polling time |

---

## 🌍 Environment Limits

- `extract("./file.pdf")`, `submit("./file.pdf")`, `flashExtract("./file.pdf")`, and all save helpers rely on `node:fs/promises` and `node:path`. Use them in Node.js, Bun, or Deno with Node compatibility.
- Standard browser runtimes are not a first-class target today because the SDK imports Node modules for local-file and save helpers. If your toolchain can bundle it anyway, stick to URL-based inputs and in-memory results.
- The `MINERU_TOKEN` fallback is Node-style. In browsers, pass the token explicitly: `new MinerU("your-api-token")`.
- Flash results only contain Markdown. `saveDocx()`, `saveHtml()`, `saveLatex()`, and `saveAll()` require a full-feature result that has already reached `state === "done"`.

---

## 📖 Detailed Usage

### Full Feature Extraction Options

```typescript
import { MinerU, saveAll } from "mineru-open-sdk";

const client = new MinerU("your-api-token");

const result = await client.extract("./paper.pdf", {
  model: "vlm",              // "vlm" | "pipeline" | "html"
  ocr: true,
  formula: true,
  table: true,
  language: "en",
  pages: "1-20",
  extraFormats: ["docx"],
  timeout: 600,
});

await saveAll(result, "./output");
```

### Batch Processing

```typescript
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: ${result.state}`);
}
```

### Batch With Per-File Pages

```typescript
const batchId = await client.submitBatch(["a.pdf", "b.pdf"], {
  fileParams: {
    "a.pdf": { pages: "1-5" },
    "b.pdf": { pages: "10-20" },
  },
});
```

### Web Crawling

```typescript
const result = await client.crawl("https://www.baidu.com");
console.log(result.markdown);
```

---

## 🔄 `submit()` / `getBatch()` Semantics

The important rule is simple:

- `submit()` returns a **batch ID**
- `submitBatch()` also returns a **batch ID**
- the normal async flow is therefore `submit(...) -> getBatch(batchId)`
- `getTask(taskId)` is only useful when you obtained a real task ID from somewhere else, not from `submit()`

### Why `submit()` returns a batch ID

The SDK deliberately normalizes both single-URL and local-file submissions onto batch semantics:

- a single URL is submitted through the batch endpoint internally
- a single local file is uploaded through the batch upload flow internally
- that means `submit()` always gives you a batch-oriented handle

### `submitBatch()` returns what

- `submitBatch([...])` always returns a **batch ID**
- `submitBatch()` does **not** allow mixing URLs and local files in one call
- `extractBatch()` does allow mixed sources because it internally creates separate batches and merges the completed results for you

### Recommended polling pattern

```typescript
const batchId = await client.submit("https://example.com/report.pdf");

while (true) {
  const [result] = await client.getBatch(batchId);
  if (result && (result.state === "done" || result.state === "failed")) {
    break;
  }
}
```

### What the query methods populate

- If a queried result is still pending/running, you only get metadata such as `state`, `progress`, `taskId`, and possible error fields
- Once a result reaches `state === "done"` and includes a zip URL, `getBatch()` automatically downloads and parses the zip so `markdown`, `images`, `contentList`, `docx`, `html`, and `latex` become available

---

## 🤖 Integration for AI Agents

The SDK exposes enough state for agent loops via `result.state` and `result.progress`.

```typescript
const batchId = await client.submit("https://example.com/large-report.pdf");

const [result] = await client.getBatch(batchId);
if (result?.state === "done") {
  processMarkdown(result.markdown);
}
```

---

## 📄 License

This project is licensed under the Apache-2.0 License.

## 🔗 Links

- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/apiManage/docs)
