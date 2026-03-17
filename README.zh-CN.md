# mineru

[English](./README.md)

[MinerU](https://mineru.net) 文档解析 API 的 TypeScript/JavaScript SDK。一行代码将文档转为 Markdown。

## 安装

```bash
npm install mineru
```

## 快速开始

```bash
export MINERU_TOKEN="your-api-token"   # 从 https://mineru.net 获取
```

```typescript
import { MinerU } from "mineru";

const md = (await new MinerU().extract("https://example.com/report.pdf")).markdown;
```

就这么简单。`extract()` 提交任务、轮询等待、下载结果 ZIP 并解析出 Markdown —— 一次异步调用搞定。

## 使用方法

### 解析单个文档

```typescript
import { MinerU } from "mineru";

const client = new MinerU();
const result = await client.extract("https://example.com/paper.pdf");
console.log(result.markdown);
console.log(result.contentList);  // 结构化 JSON
console.log(result.images);       // 提取的图片列表
```

### 本地文件

本地文件会自动上传：

```typescript
const result = await client.extract("./report.pdf");
```

### 导出额外格式

在默认的 Markdown + JSON 之外，还可以请求其他格式：

```typescript
import { saveMarkdown, saveDocx, saveHtml, saveLatex, saveAll } from "mineru";

const result = await client.extract("https://example.com/report.pdf", {
  extraFormats: ["docx", "html", "latex"],
});

await saveMarkdown(result, "./output/report.md");  // markdown + images/ 目录
await saveDocx(result, "./output/report.docx");
await saveHtml(result, "./output/report.html");
await saveLatex(result, "./output/report.tex");
await saveAll(result, "./output/full/");            // 解压完整 ZIP
```

### 抓取网页

`crawl()` 是 `extract(url, { model: "html" })` 的简写：

```typescript
const result = await client.crawl("https://news.example.com/article/123");
console.log(result.markdown);
```

### 批量解析

`extractBatch()` 一次性提交所有任务，先完成的先返回：

```typescript
for await (const result of client.extractBatch([
  "https://example.com/ch1.pdf",
  "https://example.com/ch2.pdf",
  "https://example.com/ch3.pdf",
])) {
  console.log(`${result.filename}: ${result.markdown?.slice(0, 200)}`);
}
```

批量抓取网页也一样：

```typescript
for await (const result of client.crawlBatch(["https://a.com/1", "https://a.com/2"])) {
  console.log(result.markdown?.slice(0, 200));
}
```

### 异步提交 + 查询

适用于后台服务或需要将提交和轮询解耦的场景。`submit()` 返回一个任务 ID 字符串，随你怎么存：

```typescript
const taskId = await client.submit("https://example.com/big-report.pdf", { model: "vlm" });
console.log(taskId);  // "a90e6ab6-44f3-4554-..."

// 稍后（同一进程、不同脚本，都行）：
const result = await client.getTask(taskId);
if (result.state === "done") {
  console.log(result.markdown?.slice(0, 500));
} else {
  console.log(`状态: ${result.state}, 进度: ${result.progress}`);
}
```

批量版本：

```typescript
const batchId = await client.submitBatch(["a.pdf", "b.pdf", "c.pdf"]);

const results = await client.getBatch(batchId);
for (const r of results) {
  console.log(`${r.filename}: ${r.state}`);
}
```

### 完整参数

```typescript
const result = await client.extract("./paper.pdf", {
  model: "vlm",              // "pipeline" | "vlm" | "html"（不传则自动推断）
  ocr: true,                 // 对扫描件启用 OCR
  formula: true,             // 公式识别（默认: true）
  table: true,               // 表格识别（默认: true）
  language: "en",            // 文档语言（默认: "ch"）
  pages: "1-20",             // 页码范围，如 "1-10,15" 或 "2--2"
  extraFormats: ["docx"],    // 同时导出 docx / html / latex
  timeout: 600,              // 最大等待秒数（默认: 300）
});
```

### Flash 模式（无需 token）

Flash 模式使用轻量级 API，速度优先。无需 API token，仅输出 Markdown —— 不支持模型选择和额外格式导出。

```typescript
const client = new MinerU();  // 无需 token
const result = await client.flashExtract("https://example.com/report.pdf");
console.log(result.markdown);
```

带参数：

```typescript
const result = await client.flashExtract("./report.pdf", {
  language: "en",       // 文档语言（默认: "ch"）
  pageRange: "1-10",    // 页码范围
  timeout: 300,         // 最大等待秒数（默认: 300）
});
await saveMarkdown(result, "./output/report.md");
```

Flash 模式限制：最多 50 页，最大 10 MB。

`new MinerU("token")` 创建的客户端同时支持 `extract()` 和 `flashExtract()`。`new MinerU()` 无 token 创建的客户端仅支持 `flashExtract()`，调用标准方法会抛出 `NoAuthClientError`。

### 来源标识

每个 API 请求会自动携带 `source` header 标识调用来源，默认值为 `open-api-sdk-js`。如果你基于 SDK 构建自己的服务，可以覆盖它：

```typescript
const client = new MinerU("token");
client.setSource("my-backend-service");
```

### CommonJS（require）

```javascript
const { MinerU } = require("mineru");

async function main() {
  const client = new MinerU();
  const result = await client.extract("https://example.com/doc.pdf");
  console.log(result.markdown);
}
main();
```

## API 参考

### 方法

| 方法 | 输入 | 输出 | 是否阻塞 | 用途 |
|------|------|------|----------|------|
| `extract(source, opts?)` | `string` | `Promise<ExtractResult>` | 是（await） | 单个文档 |
| `extractBatch(sources, opts?)` | `string[]` | `AsyncGenerator<ExtractResult>` | 是（for await） | 批量文档 |
| `crawl(url, opts?)` | `string` | `Promise<ExtractResult>` | 是（await） | 单个网页 |
| `crawlBatch(urls, opts?)` | `string[]` | `AsyncGenerator<ExtractResult>` | 是（for await） | 批量网页 |
| `submit(source, opts?)` | `string` | `Promise<string>`（task_id） | 否 | 异步提交 |
| `submitBatch(sources, opts?)` | `string[]` | `Promise<string>`（batch_id） | 否 | 异步批量提交 |
| `getTask(taskId)` | `string` | `Promise<ExtractResult>` | 否 | 查询任务状态 |
| `getBatch(batchId)` | `string` | `Promise<ExtractResult[]>` | 否 | 查询批量状态 |
| `flashExtract(source, opts?)` | `string` | `Promise<ExtractResult>` | 是（await） | Flash 模式（无需 token） |

### ExtractResult

| 字段 | 类型 | 说明 |
|------|------|------|
| `markdown` | `string \| null` | 提取的 Markdown 文本 |
| `contentList` | `object[] \| null` | 结构化 JSON 内容 |
| `images` | `Image[]` | 提取的图片 |
| `docx` | `Uint8Array \| null` | Docx 字节（需要 `extraFormats`） |
| `html` | `string \| null` | HTML 文本（需要 `extraFormats`） |
| `latex` | `string \| null` | LaTeX 文本（需要 `extraFormats`） |
| `state` | `string` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `error` | `string \| null` | `state === "failed"` 时的错误信息 |
| `progress` | `Progress \| null` | `state === "running"` 时的页面进度 |

保存方法：`saveMarkdown(result, path)`、`saveDocx(result, path)`、`saveHtml(result, path)`、`saveLatex(result, path)`、`saveAll(result, dir)`。

### 模型版本

| `model` | 说明 |
|---------|------|
| `undefined`（默认） | 自动推断：`.html` → `"html"`，其他 → `"vlm"` |
| `"vlm"` | 视觉语言模型（推荐） |
| `"pipeline"` | 经典版面分析 |
| `"html"` | 网页提取 |

## 环境要求

- Node.js >= 18（使用原生 `fetch`）
- 同样支持 Bun 和 Deno

## 许可证

Apache-2.0
