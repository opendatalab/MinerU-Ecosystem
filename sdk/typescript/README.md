# MinerU Open API SDK (JS/TS)

[![npm version](https://badge.fury.io/js/mineru.svg)](https://badge.fury.io/js/mineru)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/sdk/go-js/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free TypeScript/JavaScript library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one line of code.

Works in Node.js (18+), Bun, Deno, and the Browser.

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Flash Mode (No Auth)**: Extract text instantly without an API token.
- **Full Feature Mode**: Comprehensive extraction with layout preservation, images, and formula support.
- **Async & Batch**: Native async generators for processing multiple documents efficiently.

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

// No token needed for Flash Mode
const client = new MinerU();
const result = await client.flashExtract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");

console.log(result.markdown);
```

### 2. Full Feature Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.
```typescript
import { MinerU } from "mineru-open-sdk";

// Get your free token from https://mineru.net
const client = new MinerU("your-api-token");
const result = await client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");

console.log(result.markdown);
console.log(result.images); // Access extracted images
```

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

## 📖 Detailed Usage

### Full Feature Extraction Options
```typescript
import { saveAll } from "mineru-open-sdk";

const result = await client.extract("./paper.pdf", {
  model: "vlm",              // "vlm" | "pipeline" | "html"
  ocr: true,                 // Enable OCR for scanned documents
  formula: true,             // Formula recognition
  table: true,               // Table recognition
  language: "en",            // "ch" | "en" | etc.
  pages: "1-20",             // Page range
  extraFormats: ["docx"],    // Export as docx, html, or latex
  timeout: 600,
});

await saveAll(result, "./output/"); // Save markdown and all assets
```

### Batch Processing
```typescript
// Yields results as they complete
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: Done`);
}
```

### Web Crawling
```typescript
const result = await client.crawl("https://www.baidu.com");
console.log(result.markdown);
```

---

## 🤖 Integration for AI Agents

Designed for seamless integration into AI workflows. All status and progress info is accessible via `result.state` and `result.progress`.

```typescript
const taskId = await client.submit("large-report.pdf");
// ... later ...
const result = await client.getTask(taskId);
if (result.state === "done") {
  processMarkdown(result.markdown);
}
```

---

## 📄 License
This project is licensed under the Apache-2.0 License.

## 🔗 Links
- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/docs)
