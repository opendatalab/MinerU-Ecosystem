# MinerU Open API SDK (JS/TS)

[![npm version](https://badge.fury.io/js/mineru.svg)](https://badge.fury.io/js/mineru)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/OpenDataLab/mineru-open-sdk-js/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费的 TypeScript/JavaScript 库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一行代码，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

支持 Node.js (18+)、Bun、Deno 以及浏览器环境。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **极速模式 (No Auth)**：无需 API Token 即可立即提取。
- **全功能模式**：提供完整的版式保留、图片、表格及公式支持。
- **异步与批量**：原生支持异步生成器（Async Generators），高效处理多份文档。

---

## 📦 安装指南

```bash
npm install mineru
```

---

## 🛠️ 快速上手

### 1. 极速模式 (Flash Extract - 免登录，Markdown 唯一)
适合快速预览。无需配置 Token。
```typescript
import { MinerU } from "mineru";

// 极速模式无需传入 Token
const client = new MinerU();
const result = await client.flashExtract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");

console.log(result.markdown);
```

### 2. 全功能模式 (Full Feature Extract - 需登录)
支持超大文件、丰富的资产（图片/表格）及多种输出格式。
```typescript
import { MinerU } from "mineru";

// 从 https://mineru.net 获取免费 Token
const client = new MinerU("your-api-token");
const result = await client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf");

console.log(result.markdown);
console.log(result.images); // 获取提取出的图片列表
```

---

## 📊 模式对比

| 特性 | 极速模式 (Flash) | 全功能模式 (Full Feature) |
| :--- | :--- | :--- |
| **身份认证** | **免登录 (No Auth)** | **需登录 (Token)** |
| **处理速度** | 极速 | 标准 |
| **文件大小上限** | 最大 10 MB | 最大 200 MB |
| **文件页数上限** | 最大 20 页 | 最大 600 页 |
| **支持格式** | PDF, 图片, Docx, PPTx, Excel | PDF, 图片, Doc/x, Ppt/x, Html |
| **内容完整度** | 仅文本 (图片、表格、公式显示占位符) | 完整资源 (图片、表格、公式全部保留) |
| **输出格式** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## 📖 详细用法

### 全功能提取选项
```typescript
import { saveAll } from "mineru";

const result = await client.extract("./论文.pdf", {
  model: "vlm",              // "vlm" | "pipeline" | "html"
  ocr: true,                 // 启用 OCR 识别扫描件
  formula: true,             // 公式识别
  table: true,               // 表格识别
  language: "en",            // "ch" | "en" | 等
  pages: "1-20",             // 页码范围
  extraFormats: ["docx"],    // 额外导出为 docx, html, 或 latex
  timeout: 600,
});

await saveAll(result, "./output/"); // 保存 Markdown 和所有相关资源
```

### 批量处理
```typescript
// 边处理边返回结果
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: 已完成`);
}
```

### 网页爬取 (Crawl)
```typescript
const result = await client.crawl("https://www.baidu.com");
console.log(result.markdown);
```

---

## 🤖 AI Agent 自动化集成

本 SDK 设计时充分考虑了 AI 工作流集成。您可以通过 `result.state` 和 `result.progress` 轻松监控任务状态。

```typescript
const taskId = await client.submit("大报告.pdf");
// ... 稍后 ...
const result = await client.getTask(taskId);
if (result.state === "done") {
  processMarkdown(result.markdown);
}
```

---

## 📄 开源协议
本项目采用 Apache-2.0 协议。

## 🔗 相关链接
- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
