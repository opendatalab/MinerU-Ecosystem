# mineru

[中文文档](./README.zh-CN.md)

TypeScript/JavaScript SDK for the [MinerU](https://mineru.net) document extraction API. One line to turn documents into Markdown.

## Install

```bash
npm install mineru
```

## Quick Start

```bash
export MINERU_TOKEN="your-api-token"   # get it from https://mineru.net
```

```typescript
import { MinerU } from "mineru";

const md = (await new MinerU().extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")).markdown;
```

That's it. `extract()` submits the task, polls until done, downloads the result zip, and parses out the markdown — all in one async call.

## Usage

### Parse a single document

```typescript
import { MinerU } from "mineru";

const client = new MinerU();
const result = await client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");
console.log(result.markdown);
console.log(result.contentList);  // structured JSON
console.log(result.images);       // list of extracted images
```

### Local files

Local files are uploaded automatically:

```typescript
const result = await client.extract("./report.pdf");
```

### Extra format export

Request additional formats alongside the default markdown + JSON:

```typescript
import { saveMarkdown, saveDocx, saveHtml, saveLatex, saveAll } from "mineru";

const result = await client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf", {
  extraFormats: ["docx", "html", "latex"],
});

await saveMarkdown(result, "./output/report.md");  // markdown + images/ dir
await saveDocx(result, "./output/report.docx");
await saveHtml(result, "./output/report.html");
await saveLatex(result, "./output/report.tex");
await saveAll(result, "./output/full/");            // extract the full zip
```

### Crawl a web page

`crawl()` is a shorthand for `extract(url, { model: "html" })`:

```typescript
const result = await client.crawl("https://news.example.com/article/123");
console.log(result.markdown);
```

### Batch extraction

`extractBatch()` submits all tasks at once and yields results as each completes — first done, first yielded:

```typescript
for await (const result of client.extractBatch([
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
])) {
  console.log(`${result.filename}: ${result.markdown?.slice(0, 200)}`);
}
```

Batch crawling works the same way:

```typescript
for await (const result of client.crawlBatch(["https://a.com/1", "https://a.com/2"])) {
  console.log(result.markdown?.slice(0, 200));
}
```

### Async submit + query

For background services or when you need to decouple submission from polling. `submit()` returns a plain task ID string — store it however you like:

```typescript
const taskId = await client.submit("https://cdn-mineru.openxlab.org.cn/demo/example.pdf", { model: "vlm" });
console.log(taskId);  // "a90e6ab6-44f3-4554-..."

// Later (same process, different script, whatever):
const result = await client.getTask(taskId);
if (result.state === "done") {
  console.log(result.markdown?.slice(0, 500));
} else {
  console.log(`State: ${result.state}, progress: ${result.progress}`);
}
```

Batch version:

```typescript
const batchId = await client.submitBatch(["a.pdf", "b.pdf", "c.pdf"]);

const results = await client.getBatch(batchId);
for (const r of results) {
  console.log(`${r.filename}: ${r.state}`);
}
```

### Full options

```typescript
const result = await client.extract("./paper.pdf", {
  model: "vlm",              // "pipeline" | "vlm" | "html" (auto-inferred if omitted)
  ocr: true,                 // enable OCR for scanned documents
  formula: true,             // formula recognition (default: true)
  table: true,               // table recognition (default: true)
  language: "en",            // document language (default: "ch")
  pages: "1-20",             // page range, e.g. "1-10,15" or "2--2"
  extraFormats: ["docx"],    // also export as docx / html / latex
  timeout: 600,              // max seconds to wait (default: 300)
});
```

### Flash mode (no token required)

Flash mode uses a lightweight API optimised for speed. No API token needed, only outputs Markdown — no model selection, no extra formats.

```typescript
const client = new MinerU();  // no token needed
const result = await client.flashExtract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");
console.log(result.markdown);
```

With options:

```typescript
const result = await client.flashExtract("./report.pdf", {
  language: "en",       // document language (default: "ch")
  pageRange: "1-10",    // page range
  timeout: 300,         // max seconds to wait (default: 300)
});
await saveMarkdown(result, "./output/report.md");
```

Flash mode limitations: max 50 pages, max 10 MB file size.

When you create `new MinerU("token")`, both `extract()` and `flashExtract()` are available. When you create `new MinerU()` without a token, only `flashExtract()` works — calling standard methods throws `NoAuthClientError`.

### Source tracking

Every API request includes a `source` header to identify the calling application. The default is `open-api-sdk-js`. Override it if you're building your own service on top of the SDK:

```typescript
const client = new MinerU("token");
client.setSource("my-backend-service");
```

### CommonJS (require)

```javascript
const { MinerU } = require("mineru");

async function main() {
  const client = new MinerU();
  const result = await client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");
  console.log(result.markdown);
}
main();
```

## API Reference

### Methods

| Method | Input | Output | Blocking | Use case |
|--------|-------|--------|----------|----------|
| `extract(source, opts?)` | `string` | `Promise<ExtractResult>` | Yes (await) | Single document |
| `extractBatch(sources, opts?)` | `string[]` | `AsyncGenerator<ExtractResult>` | Yes (for await) | Batch documents |
| `crawl(url, opts?)` | `string` | `Promise<ExtractResult>` | Yes (await) | Single web page |
| `crawlBatch(urls, opts?)` | `string[]` | `AsyncGenerator<ExtractResult>` | Yes (for await) | Batch web pages |
| `submit(source, opts?)` | `string` | `Promise<string>` (task_id) | No | Async submit |
| `submitBatch(sources, opts?)` | `string[]` | `Promise<string>` (batch_id) | No | Async batch submit |
| `getTask(taskId)` | `string` | `Promise<ExtractResult>` | No | Query task state |
| `getBatch(batchId)` | `string` | `Promise<ExtractResult[]>` | No | Query batch state |
| `flashExtract(source, opts?)` | `string` | `Promise<ExtractResult>` | Yes (await) | Flash mode (no token) |

### ExtractResult

| Field | Type | Description |
|-------|------|-------------|
| `markdown` | `string \| null` | Extracted markdown text |
| `contentList` | `object[] \| null` | Structured JSON content |
| `images` | `Image[]` | Extracted images |
| `docx` | `Uint8Array \| null` | Docx bytes (requires `extraFormats`) |
| `html` | `string \| null` | HTML text (requires `extraFormats`) |
| `latex` | `string \| null` | LaTeX text (requires `extraFormats`) |
| `state` | `string` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `error` | `string \| null` | Error message when `state === "failed"` |
| `progress` | `Progress \| null` | Page progress when `state === "running"` |

Save helpers: `saveMarkdown(result, path)`, `saveDocx(result, path)`, `saveHtml(result, path)`, `saveLatex(result, path)`, `saveAll(result, dir)`.

### Model versions

| `model` | Description |
|---------|-------------|
| `undefined` (default) | Auto-infer: `.html` → `"html"`, everything else → `"vlm"` |
| `"vlm"` | Vision-language model (recommended) |
| `"pipeline"` | Classic layout analysis |
| `"html"` | Web page extraction |

## Requirements

- Node.js >= 18 (uses native `fetch`)
- Also works with Bun and Deno

## License

Apache-2.0
