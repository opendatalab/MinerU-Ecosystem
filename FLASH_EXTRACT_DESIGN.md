# FlashExtract 技术方案

> 最后更新：2026-03-16

## 一、背景

MinerU API 新增了 Agent 轻量解析接口（下称 Flash API），面向 AI Agent 场景，提供免登录、快速的文档解析能力。需要在现有 SDK（Go / Python / TypeScript）和 CLI 中支持该接口。

### Flash API vs 标准 API 核心差异

| 维度 | 标准 API (v4) | Flash API (v1/agent) |
|------|--------------|---------------------|
| 认证 | `Bearer token` 必须 | 无需认证，IP 限频 |
| Base URL | `https://mineru.net/api/v4` | `https://mineru.net/api/v1/agent` |
| 提交端点 | URL/文件统一 `POST /extract/task` | URL → `POST /parse/url`；文件 → `POST /parse/file` |
| 参数 | model, ocr, formula, table, language, pages, extra_formats | 仅 language, page_range (+url/file_name) |
| 输出 | zip 包（md + content_list + images + docx/html/latex） | 仅 `markdown_url`（CDN 链接） |
| 查询端点 | `GET /extract/task/{id}` → `zip_url` | `GET /parse/{task_id}` → `markdown_url` |
| 任务状态 | pending, running, done, failed, converting | waiting-file, uploading, pending, running, done, failed |
| 文件上传 | `POST /file-urls/batch` → PUT（支持多文件） | `POST /parse/file` → PUT（单文件） |
| 批量 | 支持 batch | 不支持 |
| 文件限制 | 宽松 | 10MB / 50 页 |

### Flash API 端点详情

| 端点 | 方法 | 用途 |
|------|------|------|
| `/parse/url` | POST | 提交 URL 解析任务，返回 `task_id` |
| `/parse/file` | POST | 获取签名上传 URL，返回 `task_id` + `file_url` |
| `/parse/{task_id}` | GET | 查询任务状态和结果 |

### Flash API 专属错误码

| 错误码 | 说明 | 应对策略 |
|--------|------|---------|
| -30001 | 文件大小超出限制（10MB） | 使用标准 API 或拆分文件 |
| -30002 | 不支持该文件类型 | 上传 PDF/图片/Doc/PPT/HTML |
| -30003 | 文件页数超出限制（50 页） | 使用标准 API 或指定 page_range |
| -30004 | 请求参数错误 | 检查必填参数 |

---

## 二、架构设计

### 2.1 核心原则：一个 Client，两个 API 层

```
Client (一个类型)
├── api      *apiClient       // 标准 API 层，带 token；New() 时创建，NewFlash() 时为 nil
├── flashApi *flashApiClient  // Flash API 层，无 token；始终创建
```

- `New("token")` → `api` 有值，`flashApi` 有值 → `Extract()` 和 `FlashExtract()` 都能用
- `NewFlash()` → `api` 为 nil，`flashApi` 有值 → 只有 `FlashExtract()` 能用

两条路径天然隔离，不需要在业务方法里逐个加校验。

### 2.2 误调守卫

`NewFlash()` 返回的 client 调用 `Extract()` 等标准方法时，走到 `c.api.post()`，此时 `c.api == nil`。

守卫方式：在 `apiClient.post()` 和 `apiClient.get()` 内检查 nil receiver：

```go
func (a *apiClient) post(ctx context.Context, path string, payload any) (json.RawMessage, error) {
    if a == nil {
        return nil, &ParamError{APIError{
            Code:    "NO_AUTH",
            Message: "this operation requires an authenticated client; use mineru.New(token) instead of NewFlash()",
        }}
    }
    // ... 原有逻辑不变
}
```

**为什么用 `ParamError` 而非 `AuthError`：** 这不是"认证失败"（token 过期/无效），而是"用错了 API"——编程错误。CLI 的 `exitcode.Wrap` 匹配 `ParamError` 给出的 hint（"Check your command arguments"）比 `AuthError` 的 hint（"Token is invalid or expired"）更合理。

**守卫只需加两处**（`post` 和 `get`），所有标准方法（Extract, ExtractBatch, Crawl, CrawlBatch, Submit, SubmitBatch, GetTask, GetBatch）自动受保护，未来新增标准方法也无需额外处理。

### 2.3 构造器设计

```go
// 标准模式（不变）——需要 token，所有方法可用
func New(token string, opts ...ClientOption) (*Client, error)

// Flash 模式（新增）——无需 token，只有 FlashExtract 可用
func NewFlash(opts ...ClientOption) *Client
```

`New()` 的行为完全不变：空 token 仍然返回 `AuthError`，不破坏现有用户。

### 2.4 FlashExtract 方法签名

```go
func (c *Client) FlashExtract(ctx context.Context, source string, opts ...FlashExtractOption) (*ExtractResult, error)
```

内部流程：
1. 判断 source 是 URL 还是本地文件路径
2. URL → `POST /parse/url`；文件 → `POST /parse/file` + PUT 上传
3. 轮询 `GET /parse/{task_id}`，处理 waiting-file/uploading/pending/running 状态
4. 完成后下载 `markdown_url` 内容，填入 `ExtractResult.Markdown`
5. 返回结果

### 2.5 参数设计

标准方法用 `ExtractOption`，Flash 方法用独立的 `FlashExtractOption`：

```go
type FlashExtractOption func(*flashExtractConfig)

type flashExtractConfig struct {
    language string        // 默认 "ch"
    pages    *string       // 页码范围，如 "1-10"
    timeout  time.Duration // 轮询超时，默认 5min
}

func WithFlashLanguage(lang string) FlashExtractOption
func WithFlashPages(pages string) FlashExtractOption
func WithFlashTimeout(d time.Duration) FlashExtractOption
```

Go/TypeScript 通过类型系统在编译期阻止传入不兼容参数（如 `WithModel`）。Python 通过独立的 kwargs 签名在调用时立即报 TypeError。

### 2.6 返回类型

复用 `ExtractResult`，不新增字段。SDK 内部下载 `markdown_url` 的内容后直接填入 `Markdown` 字段，CDN 链接不暴露给用户（有过期时间，暴露无意义）。

Flash 模式下：
- `Markdown` — 有值（SDK 自动下载填入）
- `Images`, `ContentList`, `Docx`, `HTML`, `LaTeX` — 均为零值
- `ZipURL` — 空
- `Progress` — 轮询期间有值（`extracted_pages` / `total_pages`）

### 2.7 错误处理

在 `errors.go` 中新增 Flash 专属错误类型：

```go
type FlashFileTooLargeError struct{ APIError }  // -30001
type FlashUnsupportedTypeError struct{ APIError } // -30002
type FlashPageLimitError struct{ APIError }      // -30003
type FlashParamError struct{ APIError }          // -30004
```

在 `errorForCode()` 中新增映射。CLI 的 `exitcode.Wrap` 相应扩展。

---

## 三、Go SDK 改动清单

| 文件 | 改动 |
|------|------|
| `options.go` | 新增 `FlashExtractOption` 类型及 `WithFlashLanguage` / `WithFlashPages` / `WithFlashTimeout` |
| `models.go` | `ExtractResult` 结构体不变；`SaveDocx/SaveHTML/SaveLaTeX/SaveAll` 错误信息改为通用措辞（如 "no docx content available"），不假设调用模式 |
| `errors.go` | 新增 Flash 专属错误类型 + `errorForCode()` 映射 |
| `api.go` | `post()` / `get()` 新增 nil receiver 守卫 |
| **`flash_api.go`** (新增) | `flashApiClient` 结构体，实现 `postFlash()` / `getFlash()` / `putFile()` / `downloadMarkdown()` |
| **`flash.go`** (新增) | `NewFlash()` 构造器；`FlashExtract()` 方法；`submitFlashURL()` / `submitFlashFile()` / `waitFlash()` / `parseFlashResult()` |
| `client.go` | `Client` 结构体新增 `flashApi` 字段；`New()` 同时初始化 `flashApi` |

---

## 四、CLI 改动

### 4.1 新增 `flash-extract` 子命令

独立子命令而非 `--flash` flag，原因：
- Flash 只有 `extract` 能用，`crawl` 不能 — flag 挂在 `extract` 上语义别扭
- 与 `--model`、`--ocr`、`--no-formula`、`--no-table`、`--format` 全部不兼容 — 组合校验复杂且易出错
- 独立子命令有自己干净的参数集，`--help` 清晰明了

```
Usage:
  mineru-open-api-cli flash-extract <file-or-url> [flags]

Examples:
  mineru-open-api-cli flash-extract report.pdf                     # markdown to stdout
  mineru-open-api-cli flash-extract report.pdf -o ./out/           # save to file
  mineru-open-api-cli flash-extract https://example.com/doc.pdf    # URL mode
  mineru-open-api-cli flash-extract report.pdf --language en       # specify language
  mineru-open-api-cli flash-extract report.pdf --pages 1-10        # page range

Flags:
      --language string   Document language (default "ch")
      --pages string      Page range, e.g. '1-10'
  -o, --output string     Output path; omit for stdout
      --timeout int       Timeout in seconds (default 300)
  -h, --help              help for flash-extract
```

### 4.2 CLI 改动文件

| 文件 | 改动 |
|------|------|
| **`cmd/flash_extract.go`** (新增) | `flash-extract` 子命令实现 |
| `cmd/root.go` | 无改动（全局 flags `--base-url` / `--verbose` 自动继承） |
| `internal/exitcode/exitcode.go` | 新增 Flash 专属错误码的映射和 hint |

### 4.3 flash-extract 不需要 auth

```go
func runFlashExtract(cmd *cobra.Command, args []string) error {
    // 不调 config.ResolveToken()，不需要 token
    client := mineru.NewFlash(clientOpts...)
    result, err := client.FlashExtract(ctx, source, opts...)
    // ...
}
```

---

## 五、跨语言 API 一致性

### 5.1 命名约定

| 层 | Go | Python | TypeScript | CLI |
|----|-----|--------|-----------|-----|
| 构造器 | `NewFlash()` | `MinerU()` (无 token) | `new MinerU()` | — |
| 方法名 | `FlashExtract()` | `flash_extract()` | `flashExtract()` | `flash-extract` |
| 参数-语言 | `WithFlashLanguage("en")` | `language="en"` | `{ language: "en" }` | `--language en` |
| 参数-页码 | `WithFlashPages("1-10")` | `page_range="1-10"` | `{ pageRange: "1-10" }` | `--pages 1-10` |
| 返回类型 | `*ExtractResult` | `ExtractResult` | `ExtractResult` | stdout / -o file |

### 5.2 各语言用法示例

**Go:**
```go
client := mineru.NewFlash()
result, err := client.FlashExtract(ctx, "report.pdf")
fmt.Println(result.Markdown)
```

**Python:**
```python
client = MinerU()
result = client.flash_extract("report.pdf")
print(result.markdown)
```

**TypeScript:**
```typescript
const client = new MinerU();
const result = await client.flashExtract("report.pdf");
console.log(result.markdown);
```

**CLI:**
```bash
mineru-open-api-cli flash-extract report.pdf
```

### 5.3 参数限制（编译期 vs 运行时）

| 语言 | 机制 | 传入不兼容参数的结果 |
|------|------|---------------------|
| Go | `FlashExtractOption` 独立类型 | 编译报错 |
| TypeScript | `FlashExtractOptions` 独立 interface | tsc 编译报错 |
| Python | `flash_extract()` 显式 kwargs | 立即 TypeError |

---

## 六、实施路线

| 阶段 | 内容 | 预计产出 |
|------|------|---------|
| **Phase 1** | Go SDK 新增 FlashExtract | `flash.go`, `flash_api.go`, options/models/errors 扩展 |
| **Phase 2** | CLI 新增 flash-extract 子命令 | `cmd/flash_extract.go`, exitcode 扩展 |
| **Phase 3** | Python SDK 新增 flash_extract | client/models/exceptions 扩展 |
| **Phase 4** | TypeScript SDK 新增 flashExtract | client/models/errors 扩展 |

Phase 1 和 Phase 2 可以在同一个开发周期内完成（Go SDK 改完后 CLI 直接集成）。Phase 3 和 Phase 4 照搬相同模式。
