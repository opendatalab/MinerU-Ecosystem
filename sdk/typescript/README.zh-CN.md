# MinerU Open API SDK (JS/TS)

[![npm version](https://badge.fury.io/js/mineru-open-sdk.svg)](https://badge.fury.io/js/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费的 TypeScript/JavaScript 库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一行代码，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

当前发布包的主要目标运行时是 Node.js 18+。Bun 和 Deno 在提供 Node 兼容 API 时也可以使用。浏览器并不是当前的一等支持目标，详见下方的[环境限制](#-环境限制)。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **Agent 轻量解析 (No Auth)**：无需 API Token 即可立即提取。
- **精准解析**：提供完整的版式保留、图片、表格及公式支持。
- **阻塞式与异步原语并存**：简单流程直接用 `extract()`，需要自定义轮询时使用 `submit()` / `getTask()` / `getBatch()`。
- **内置结果保存方法**：可直接保存 Markdown、HTML、LaTeX、DOCX，或解压完整结果包。

---

## 📦 安装指南

```bash
npm install mineru-open-sdk
```

---

## 🛠️ 快速上手

### 1. Agent 轻量解析 (Flash Extract - 免登录，只支持 Markdown)
适合快速预览。无需配置 Token。

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU();
const result = await client.flashExtract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
);

console.log(result.markdown);
```

### 2. 精准解析 (Precision Extract - 需登录)
支持大文件、丰富资产（图片/表格）以及多种输出格式。

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

## 🧩 支持的公开接口

### Client 生命周期

- `new MinerU(token?: string, baseUrl = "https://mineru.net/api/v4", flashBaseUrl?: string)`
- `client.setSource("your-app")`

### 阻塞式解析接口

- `client.extract(source, options?) -> Promise<ExtractResult>`
- `client.extractBatch(sources, options?) -> AsyncGenerator<ExtractResult>`
- `client.crawl(url, options?) -> Promise<ExtractResult>`
- `client.crawlBatch(urls, options?) -> AsyncGenerator<ExtractResult>`
- `client.flashExtract(source, options?) -> Promise<ExtractResult>`

### 提交 / 查询接口

- `client.submit(source, options?) -> Promise<string>`
- `client.submitBatch(sources, options?) -> Promise<string>`
- `client.getTask(taskId) -> Promise<ExtractResult>`
- `client.getBatch(batchId) -> Promise<ExtractResult[]>`

### 结果与保存辅助方法

- `saveMarkdown(result, path, withImages = true)`
- `saveDocx(result, path)`
- `saveHtml(result, path)`
- `saveLatex(result, path)`
- `saveAll(result, dir)`
- `progressPercent(progress)`
- `progressToString(progress)`

### 常用结果字段

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

## 📊 模式对比

| 特性 | Agent 轻量解析 (Flash) | 精准解析 (Precision) |
| :--- | :--- | :--- |
| **身份认证** | **免登录 (No Auth)** | **需登录 (Token)** |
| **处理速度** | 极速 | 标准 |
| **文件大小上限** | 最大 10 MB | 最大 200 MB |
| **文件页数上限** | 最大 20 页 | 最大 600 页 |
| **支持格式** | PDF, 图片, Docx, PPTx, Excel | PDF, 图片, Doc/x, Ppt/x, Html |
| **内容完整度** | 仅文本 (图片、表格、公式显示占位符) | 完整资源 (图片、表格、公式全部保留) |
| **输出格式** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ 默认行为与参数说明

### `new MinerU(...)`

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `token` | `undefined` | 若运行时支持 `process.env`，则读取 `MINERU_TOKEN` |
| `baseUrl` | `https://mineru.net/api/v4` | 标准 API 默认地址 |
| `flashBaseUrl` | SDK 内置 flash 地址 | 可用于测试或私有部署 |

如果既没有传入 `token`，运行时里也没有可用的 `process.env.MINERU_TOKEN`，则 client 进入 **flash-only mode**：`flashExtract()` 可用，其余需要鉴权的方法会抛出 `NoAuthClientError`。

### 全功能接口

这些默认值适用于 `extract()`、`submit()`、`extractBatch()`、`submitBatch()`，除非特别说明。

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `model` | `undefined` | 根据输入自动推断：`.html` / `.htm` 走 `"html"`（发给 API 时为 `"MinerU-HTML"`），其余默认 `"vlm"` |
| `ocr` | `undefined` | 默认关闭 OCR（API 默认行为） |
| `formula` | `undefined` | 默认开启公式识别（API 默认行为） |
| `table` | `undefined` | 默认开启表格识别（API 默认行为） |
| `language` | `undefined` | 默认中文 `"ch"`（API 默认行为） |
| `pages` | `undefined` | 默认处理完整文档。仅单任务 `extract()` / `submit()` 支持 |
| `extraFormats` | `undefined` | 只返回默认 Markdown / JSON 结果 |
| `fileParams` | `undefined` | 批量方法中的 per-file 参数覆盖。key 为路径/URL，value 为 `{ pages?, ocr?, dataId? }` |
| `timeout` | `300` 秒 | `extract()` / `crawl()` 的总轮询超时 |
| `timeout` | `1800` 秒 | `extractBatch()` / `crawlBatch()` 的总轮询超时 |

### `crawl()` / `crawlBatch()`

- `crawl()` 等价于 `extract(url, { model: "html", ... })`
- `crawlBatch()` 等价于 `extractBatch(urls, { model: "html", ... })`
- `crawl()` / `crawlBatch()` 只暴露 `extraFormats` 和 `timeout`，不提供 OCR / 表格 / 公式开关

### Flash Extract

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `language` | `"ch"` | 默认中文 |
| `pageRange` | `undefined` | 默认处理 flash API 允许的完整页范围 |
| `timeout` | `300` 秒 | 总轮询超时 |

---

## 🌍 环境限制

- `extract("./file.pdf")`、`submit("./file.pdf")`、`flashExtract("./file.pdf")` 以及所有保存辅助方法都依赖 `node:fs/promises` 和 `node:path`。这部分能力应运行在 Node.js、Bun 或启用 Node 兼容层的 Deno 中。
- 标准浏览器运行时并不是当前的一等支持目标，因为 SDK 为本地文件和保存辅助方法直接引入了 Node 模块。如果你的工具链仍能正常打包它，也只建议处理 URL 输入和内存中的结果对象。
- `MINERU_TOKEN` 的环境变量回退是 Node 风格能力。浏览器里请显式传入 token：`new MinerU("your-api-token")`。
- Flash 结果只包含 Markdown。`saveDocx()`、`saveHtml()`、`saveLatex()` 和 `saveAll()` 需要使用已经完成的全功能结果。

---

## 📖 详细用法

### 全功能提取选项

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

### 批量处理

```typescript
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: ${result.state}`);
}
```

### 批量处理 - 为每个文件指定不同页码

```typescript
const batchId = await client.submitBatch(["a.pdf", "b.pdf"], {
  fileParams: {
    "a.pdf": { pages: "1-5" },
    "b.pdf": { pages: "10-20" },
  },
});
```

### 网页抓取

```typescript
const result = await client.crawl("https://www.baidu.com");
console.log(result.markdown);
```

---

## 🔄 `submit()` / `getBatch()` 语义说明

最重要的一条规则：

- `submit()` 返回的是 **batch ID**
- `submitBatch()` 返回的也是 **batch ID**
- 因此最常见的异步流程应该是 `submit(...) -> getBatch(batchId)`
- `getTask(taskId)` 只有在你已经从别处拿到真实 task ID 时才适合使用，不能假定它来自 `submit()`

### 为什么 `submit()` 返回 batch ID

SDK 在实现上刻意把单任务提交也统一到了 batch 语义：

- 单个 URL 会通过 batch endpoint 提交
- 单个本地文件会通过 batch upload 流程提交
- 所以 `submit()` 始终返回一个适合 `getBatch()` 轮询的 ID

### `submitBatch()` 返回什么

- `submitBatch([...])` 永远返回 **batch ID**
- `submitBatch()` **不支持** 在一次调用里混用 URL 和本地文件
- `extractBatch()` 支持混合输入，是因为它会在内部拆成多个 batch，再把完成结果合并为一个异步生成器输出

### 推荐轮询方式

```typescript
const batchId = await client.submit("https://example.com/report.pdf");

while (true) {
  const [result] = await client.getBatch(batchId);
  if (result && (result.state === "done" || result.state === "failed")) {
    break;
  }
}
```

### 查询接口返回结果的填充时机

- 当任务仍处于 pending / running 等非终态时，返回值主要包含 `state`、`progress`、`taskId` 以及可能的错误字段
- 当任务进入 `state === "done"` 且返回 zip 地址后，`getBatch()` 会自动下载并解析结果包，此时 `markdown`、`images`、`contentList`、`docx`、`html`、`latex` 等字段才会被填充

---

## 🤖 AI Agent 自动化集成

SDK 提供了适合 Agent 循环使用的状态字段，核心就是 `result.state` 和 `result.progress`。

```typescript
const batchId = await client.submit("https://example.com/large-report.pdf");

const [result] = await client.getBatch(batchId);
if (result?.state === "done") {
  processMarkdown(result.markdown);
}
```

---

## 📄 开源协议

本项目采用 Apache-2.0 协议。

## 🔗 相关链接

- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/apiManage/docs)
