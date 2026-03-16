# MinerU Open API CLI 技术方案

> 项目代号: `mineru-open-api-cli`
> 最后更新: 2026-03-13

---

## 1. 目标

为没有 Python/Go 运行环境的用户提供一个**零依赖、单二进制**的命令行工具，一条命令把文档变成 Markdown。

```bash
mineru-open-api-cli extract report.pdf
# markdown 内容直接输出到 stdout
```

**目标用户画像（按优先级）：**
1. AI Agent（Cursor/Copilot/自动化流水线）— 最大调用方
2. CI/CD 脚本和管道
3. 人在终端里手敲

---

## 2. 技术选型

| 维度 | 选型 | 理由 |
|------|------|------|
| **语言** | Go | 单二进制、交叉编译、复用已有 Go SDK |
| **CLI 框架** | [cobra](https://github.com/spf13/cobra) | 业界标准（kubectl/docker/gh 同款），子命令、帮助文档、shell 补全开箱即用 |
| **配置文件** | [viper](https://github.com/spf13/viper) | cobra 官方搭档，支持 YAML/TOML/ENV 多源配置合并 |
| **构建发布** | [goreleaser](https://goreleaser.com/) | 一键交叉编译 + 打包 + 投 GitHub Release + Homebrew |
| **依赖的 SDK** | `mineru-open-sdk-go` | 所有 API 调用走 SDK，CLI 只做交互层 |

> **去掉了 spinner/进度条库。** 默认输出不做任何终端美化（无 spinner、无颜色、无 ANSI），
> 见第 5 节设计决策。

---

## 3. 命令结构设计

### 3.1 命令树

```
mineru-open-api-cli
├── extract <file-or-url> [...] [flags]    # 解析文档（支持单个或多个）
├── crawl <url> [...] [flags]              # 抓取网页（支持单个或多个）
├── status <task-id>                       # 查询异步任务状态
├── auth [flags]                           # 配置 / 验证 / 查看 Token
│   ├── (default)                          # 交互式配置 token
│   ├── --verify                           # 验证当前 token 是否有效
│   └── --show                             # 显示当前 token 来源
├── completion <bash|zsh|fish|powershell>  # 生成 shell 补全脚本
└── version                                # 版本信息
```

> **设计决策：去掉独立的 `batch` 命令。**
> `extract` 和 `crawl` 都天然支持多参数，单个和批量用同一个命令，
> 用户不需要多记一个词。SDK 层面 `Extract` / `ExtractBatch` 和
> `Crawl` / `CrawlBatch` 的切换由 CLI 根据参数数量自动选择。

### 3.2 核心设计：`-o` 决定输出模式

> **设计决策：借鉴 curl 模型，`-o` 是输出模式的开关。**
>
> - 没有 `-o`：内容输出到 stdout（像 `curl <url>`）
> - 有 `-o`：内容保存到文件（像 `curl -o file <url>`）
>
> 这让 AI Agent 可以一步拿到文档内容而不需要额外读文件，
> 同时保持"存文件"场景的简洁。

```
无 -o + 单个文本格式    →  该格式内容 to stdout
无 -o + 单个二进制格式  →  报错，提示加 -o
无 -o + 多个格式        →  报错，提示加 -o
无 -o + 多文件（批量）  →  报错，提示加 -o
有 -o                   →  所有格式存文件
```

**`-f` 支持的格式：**

| `-f` 值 | 内容类型 | 可 stdout | 说明 |
|---------|---------|-----------|------|
| `md` | 文本 | ✅ | Markdown（默认） |
| `html` | 文本 | ✅ | HTML |
| `latex` | 文本 | ✅ | LaTeX |
| `json` | 文本 | ✅ | content_list 结构化 JSON |
| `docx` | 二进制 | ❌ | Word 文档，必须配合 -o |

**错误信息（三种不同场景）：**

```bash
mineru-open-api-cli extract report.pdf -f docx
# Error: docx is binary format, cannot output to stdout. Use -o to save to file.

mineru-open-api-cli extract report.pdf -f md,html
# Error: multiple formats cannot output to stdout. Use -o to save to file.

mineru-open-api-cli extract *.pdf
# Error: batch mode requires -o to specify output directory.
```

### 3.3 命令详细设计

#### `mineru-open-api-cli extract`

```
Usage:
  mineru-open-api-cli extract <file-or-url> [...] [flags]

Examples:
  # 内容到 stdout（默认 markdown）
  mineru-open-api-cli extract report.pdf
  mineru-open-api-cli extract report.pdf -f html
  mineru-open-api-cli extract report.pdf -f json
  mineru-open-api-cli extract report.pdf | head -20

  # 内容保存到文件
  mineru-open-api-cli extract report.pdf -o report.md
  mineru-open-api-cli extract report.pdf -o ./out/
  mineru-open-api-cli extract report.pdf -o ./out/ -f md,docx
  mineru-open-api-cli extract report.pdf -o ./out/ -f docx

  # 批量（必须 -o）
  mineru-open-api-cli extract *.pdf -o ./results/
  mineru-open-api-cli extract ch1.pdf ch2.pdf -o ./out/ -f md,docx
  mineru-open-api-cli extract --list files.txt -o ./results/
  ls *.pdf | mineru-open-api-cli extract --stdin-list -o ./out/

  # stdin 读取文件内容
  cat report.pdf | mineru-open-api-cli extract --stdin --stdin-name report.pdf

Flags:
  -o, --output <path>        输出路径（文件或目录）；不指定则内容输出到 stdout
  -f, --format <formats>     输出格式，逗号分隔: md,json,html,latex,docx（默认 md）
      --model <model>        模型: vlm, pipeline, html（默认自动推断）
      --ocr                  启用 OCR（扫描件场景）
      --no-formula           禁用公式识别
      --no-table             禁用表格识别
      --language <lang>      文档语言（默认 ch）
      --pages <range>        页码范围，如 "1-10,15" 或 "2--2"
      --timeout <seconds>    超时秒数；单文件默认 300，批量默认 1800（总超时）
      --list <file>          从文件读取输入列表（每行一个路径/URL）
      --stdin-list           从 stdin 读取输入列表（每行一个路径/URL）
      --stdin                从标准输入读取文件内容（需配合 --stdin-name）
      --stdin-name <name>    stdin 模式下的文件名（如 "report.pdf"）
      --concurrency <n>      批量模式并发数（默认由服务端控制）

Global Flags:
      --token <token>        API Token（优先级高于环境变量和配置文件）
      --base-url <url>       API 地址（私有化部署场景）
  -v, --verbose              调试模式，打印 HTTP 请求细节
```

**单个 vs 批量自动切换逻辑：**

```
参数数量 == 1 且无 --list/--stdin-list  →  单文件模式（调用 SDK Extract）
参数数量 > 1 或有 --list/--stdin-list   →  批量模式（调用 SDK SubmitBatch + GetBatch）
```

#### `mineru-open-api-cli crawl`

```
Usage:
  mineru-open-api-cli crawl <url> [...] [flags]

Examples:
  # 内容到 stdout
  mineru-open-api-cli crawl https://example.com/article
  mineru-open-api-cli crawl https://example.com/article -f html

  # 内容保存到文件
  mineru-open-api-cli crawl https://example.com/article -o output.md
  mineru-open-api-cli crawl https://example.com/article -o ./out/ -f md,html

  # 批量抓取（必须 -o）
  mineru-open-api-cli crawl https://a.com/1 https://a.com/2 -o ./pages/
  mineru-open-api-cli crawl --list urls.txt -o ./pages/
  cat urls.txt | mineru-open-api-cli crawl --stdin-list -o ./pages/

Flags:
  -o, --output <path>        输出路径；不指定则内容输出到 stdout
  -f, --format <formats>     输出格式: md,json,html（默认 md）
      --timeout <seconds>    超时秒数；单 URL 默认 300，批量默认 1800（总超时）
      --list <file>          从文件读取 URL 列表（每行一个）
      --stdin-list           从 stdin 读取 URL 列表
      --concurrency <n>      批量模式并发数（默认由服务端控制）
```

crawl 等同于 extract --model html，但精简了不适用于网页的 flag
（去掉 --ocr / --no-formula / --no-table / --pages / --language）。

#### `mineru-open-api-cli auth`

```
Usage:
  mineru-open-api-cli auth [flags]

Examples:
  mineru-open-api-cli auth                  # 交互式输入 token 并保存
  mineru-open-api-cli auth --verify         # 验证当前 token 是否有效
  mineru-open-api-cli auth --show           # 显示当前 token 来源

Flags:
      --verify               验证 token
      --show                 显示当前 token 配置来源
```

#### `mineru-open-api-cli status`

```
Usage:
  mineru-open-api-cli status <task-id> [flags]

Examples:
  mineru-open-api-cli status abc-123-def
  mineru-open-api-cli status abc-123-def --wait          # 阻塞等待完成
  mineru-open-api-cli status abc-123-def --wait -o ./    # 等待完成并下载结果
```

---

## 4. 认证优先级

Token 从以下来源按优先级获取（高到低）：

```
1. --token flag          命令行直接传
2. MINERU_TOKEN 环境变量  CI/CD 场景最常用
3. ~/.mineru-open-api-cli/config.yaml  mineru-open-api-cli auth 交互式保存
```

配置文件格式：

```yaml
# ~/.mineru-open-api-cli/config.yaml
token: "eyJ..."
base_url: "https://mineru.net/api/v4"   # 可选，私有化部署时覆盖
```

---

## 5. 输出设计

### 5.1 设计原则

> **设计决策：默认不做任何终端美化。**
>
> 2026 年，CLI 的最大调用方是 AI Agent，不是人。Agent 在 TTY 中调用 CLI
> 也很常见（如 Cursor Shell），TTY 检测无法区分人和 Agent。
>
> 因此：
> - 无 spinner、无 ANSI 颜色、无 `\r` 覆盖、无 Unicode 装饰符号
> - 所有状态/进度信息走 **stderr**，纯文本，每行独立完整
> - 内容/数据走 **stdout**（或 `-o` 写文件）
> - 不提供 `--json`、`--quiet`、`--no-color` 等输出模式 flag
>
> 好的 `--help` 文本比 MCP tool schema 更 Agent 友好——
> 大模型已经训练过海量 CLI help 文本，零学习成本。

### 5.2 单文件输出

**stdout 模式（无 -o）：**

```
$ mineru-open-api-cli extract report.pdf
Uploading report.pdf (2.3 MB)                  ← stderr
Parsing 12/24 pages                             ← stderr
Parsing 24/24 pages                             ← stderr
Done: 24 pages, 8.3s                            ← stderr
# Introduction                                  ← stdout（markdown 内容）
This paper presents a novel approach to...      ← stdout
```

Agent 拿到 stdout 就是 markdown 内容，stderr 的状态信息在 Agent 的终端输出里可以看到但不影响内容解析。

**指定文本格式：**

```
$ mineru-open-api-cli extract report.pdf -f html 2>/dev/null
<html><body><h1>Introduction</h1>...

$ mineru-open-api-cli extract report.pdf -f json 2>/dev/null
[{"type":"text","content":"Introduction",...},...]

$ mineru-open-api-cli crawl https://example.com -f html 2>/dev/null
<html><body>...
```

**文件模式（有 -o）：**

```
$ mineru-open-api-cli extract report.pdf -o ./out/
Uploading report.pdf (2.3 MB)
Parsing 24/24 pages
Done: ./out/report.md (15.2 KB, 24 pages, 8.3s)

$ mineru-open-api-cli extract report.pdf -o ./out/ -f md,docx
Uploading report.pdf (2.3 MB)
Parsing 24/24 pages
Done: ./out/report.md (15.2 KB), ./out/report.docx (45.2 KB), 24 pages, 8.3s
```

### 5.3 批量输出（必须 -o）

```
$ mineru-open-api-cli extract *.pdf -o ./results/
Batch: 3 files
[1/3] Done: ch1.pdf -> ./results/ch1.md (12.1 KB, 3.2s)
[2/3] Done: ch2.pdf -> ./results/ch2.md (9.8 KB, 4.1s)
[3/3] Error: ch3.pdf - file exceeds 200 MB limit (-60005)
Result: 2/3 succeeded, 1 failed (8.3s)
```

crawl 批量同理：

```
$ mineru-open-api-cli crawl https://a.com/1 https://a.com/2 -o ./pages/
Batch: 2 URLs
[1/2] Done: a.com/1 -> ./pages/a_com_1.md (8.2 KB, 2.3s)
[2/2] Done: a.com/2 -> ./pages/a_com_2.md (6.5 KB, 1.8s)
Result: 2/2 succeeded (5.1s)
```

### 5.4 错误输出

```
$ mineru-open-api-cli extract huge.pdf
Error: file exceeds 200 MB limit (-60005)

$ mineru-open-api-cli extract report.pdf
Error: token is invalid or expired (A0202). Run 'mineru-open-api-cli auth' to reconfigure.
```

错误信息走 stderr，退出码非零。Agent 通过退出码判断成败，
通过 stderr 内容获取错误详情。

---

## 6. 退出码

| 码 | 含义 | 对应 SDK 错误 |
|----|------|--------------|
| 0  | 成功 | — |
| 1  | 一般/未知错误 | `APIError` |
| 2  | 参数/用法错误 | cobra 自动处理 |
| 3  | 认证失败 | `AuthError` |
| 4  | 文件错误（不存在/太大/页数超限） | `FileTooLargeError`, `PageLimitError` |
| 5  | 服务端解析失败 | `ExtractFailedError` |
| 6  | 超时 | `TimeoutError` |
| 7  | 配额耗尽 | `QuotaExceededError` |

---

## 7. 项目结构

```
mineru-open-api-cli/
├── cmd/                          # cobra 命令定义
│   ├── root.go                   # 根命令 + global flags
│   ├── extract.go                # mineru-open-api-cli extract（含单个+批量）
│   ├── crawl.go                  # mineru-open-api-cli crawl（含单个+批量）
│   ├── auth.go                   # mineru-open-api-cli auth
│   ├── status.go                 # mineru-open-api-cli status
│   └── version.go                # mineru-open-api-cli version
├── internal/
│   ├── config/
│   │   └── config.go             # token 读取优先级链、配置文件读写
│   ├── output/
│   │   └── output.go             # stderr 状态输出（纯文本）
│   └── exitcode/
│       └── exitcode.go           # SDK error → 退出码映射
├── main.go                       # 入口：cmd.Execute()
├── go.mod
├── go.sum
├── LICENSE                       # Apache-2.0
├── README.md
├── README.zh-CN.md
├── .goreleaser.yaml              # goreleaser 构建配置
├── .github/
│   └── workflows/
│       └── release.yml           # tag 触发自动发布
├── install.sh                    # curl | sh 一键安装脚本
└── TECHNICAL_SPEC.md             # 本文档
```

> 对比原方案，`internal/output/` 从三个文件精简到一个—
> 去掉了 `color.go`（无颜色）、`progress.go`（无 spinner）、
> `printer.go`（无多模式输出）。

---

## 8. 核心实现要点

### 8.1 CLI 层 vs SDK 层职责划分

```
┌──────────────────────────────────────────────┐
│  CLI 层 (mineru-open-api-cli)                     │
│  - 参数解析、校验                              │
│  - -o 有无 → stdout/文件模式切换               │
│  - Token 优先级链                              │
│  - 进度文本（纯文本 stderr）                    │
│  - 退出码映射                                  │
│  - 文件保存路径计算                             │
└──────────────┬───────────────────────────────┘
               │  调用
┌──────────────▼───────────────────────────────┐
│  SDK 层 (mineru-open-sdk-go)                  │
│  - HTTP 通信                                   │
│  - 文件上传                                    │
│  - 轮询等待                                    │
│  - Zip 解析                                    │
│  - 错误映射                                    │
└──────────────────────────────────────────────┘
```

### 8.2 extract 命令核心流程

```go
func runExtract(cmd *cobra.Command, args []string) error {
    // 1. 收集所有输入源（args + --list + --stdin-list）
    sources := collectSources(args)

    // 2. 校验输出模式
    if outputPath == "" {
        if len(sources) > 1 {
            return fmt.Errorf("batch mode requires -o to specify output directory")
        }
        if len(formats) > 1 {
            return fmt.Errorf("multiple formats cannot output to stdout, use -o to save to file")
        }
        if isBinaryFormat(formats[0]) {
            return fmt.Errorf("%s is binary format, cannot output to stdout, use -o to save to file", formats[0])
        }
    }

    // 3. 获取 token（flag > env > config file）
    token, err := config.ResolveToken(cmd)

    // 4. 创建 SDK client
    client, err := mineru.New(token, clientOpts...)

    // 5. 根据数量自动分流
    if len(sources) == 1 {
        return runSingleExtract(client, sources[0], opts)
    }
    return runBatchExtract(client, sources, opts)
}
```

crawl 命令结构完全相同，区别仅在于调用 SDK 的 `Crawl` / `CrawlBatch` 方法。
两个命令共享 `collectSources()`、批量轮询、文件保存等公共逻辑，
通过 `internal/` 包复用，避免重复代码。

### 8.3 进度展示方案

> **设计决策：CLI 自己轮询，不用 SDK 的 `ExtractBatch` channel。**
>
> SDK 的 `ExtractBatch` 内部轮询只在任务 done/failed 时才推送结果，
> 吞掉了 running 状态的中间进度。CLI 需要实时输出每个任务的解析页数，
> 因此改用 SDK 的异步原语 `SubmitBatch` + `GetBatch` 自己做轮询循环。
> 这样 CLI 完全自控进度输出，SDK 无需为 CLI 的需求改 API。

#### 8.3.1 单文件（Submit + GetTask 轮询）

```go
taskID, _ := client.Submit(ctx, source, opts...)
interval := 2 * time.Second

for {
    result, _ := client.GetTask(ctx, taskID)
    if result.Progress != nil {
        fmt.Fprintf(os.Stderr, "Parsing %d/%d pages\n",
            result.Progress.ExtractedPages, result.Progress.TotalPages)
    }
    if result.State == "done" || result.State == "failed" {
        break
    }
    time.Sleep(interval)
    if interval < 30*time.Second {
        interval = interval * 3 / 2   // 温和退避：2s → 3s → 4.5s → ... → 30s
    }
}

// stdout 模式：内容输出到 stdout
if outputPath == "" {
    fmt.Print(result.Markdown)  // stdout
} else {
    result.SaveMarkdown(outputPath, true)
    fmt.Fprintf(os.Stderr, "Done: %s (%s, %d pages, %.1fs)\n", outputPath, ...)
}
```

#### 8.3.2 批量（SubmitBatch + GetBatch 轮询）

```go
batchID, _ := client.SubmitBatch(ctx, sources, opts...)
interval := 2 * time.Second
downloaded := map[int]bool{}

for {
    results, _ := client.GetBatch(ctx, batchID)

    for i, r := range results {
        if (r.State == "done" || r.State == "failed") && !downloaded[i] {
            downloaded[i] = true
            if r.State == "done" {
                saveResult(r, outputDir)
                fmt.Fprintf(os.Stderr, "[%d/%d] Done: %s -> %s (%s, %.1fs)\n", ...)
            } else {
                fmt.Fprintf(os.Stderr, "[%d/%d] Error: %s - %s\n", ...)
            }
        }
    }

    if len(downloaded) >= len(sources) {
        break
    }

    time.Sleep(interval)
    if interval < 30*time.Second {
        interval = interval * 3 / 2
    }
}

fmt.Fprintf(os.Stderr, "Result: %d/%d succeeded, %d failed (%.1fs)\n", ...)
```

### 8.4 超时机制

> **设计决策：批量模式下 `--timeout` 是"总超时"语义，不是 per-file。**
>
> `SubmitBatch` 是一次 API 调用把所有文件交给服务端，服务端自行调度
> 并行度。CLI 层面没有"单独取消某个文件"的能力，per-file 超时既实现不了
> 也不符合用户直觉——用户想的是"帮我跑这批文件，我最多等 30 分钟"。

| 模式 | `--timeout` 语义 | 默认值 | 实现 |
|------|-------------------|--------|------|
| **单文件** | 该文件的等待超时 | 300s（5 分钟） | `context.WithTimeout` 包住 Submit+GetTask 轮询 |
| **批量** | 整批的总超时 | 1800s（30 分钟） | 同一个 `context.WithTimeout` 包住 SubmitBatch+GetBatch 轮询 |
| **单次 HTTP** | — | 30s | SDK 内部控制，CLI 不关心 |
| **轮询间隔** | — | 2s 起步，退避到 30s | CLI 内部控制 |

批量超时后的行为：已完成的任务保留结果，未完成的标记为超时。

```
$ mineru-open-api-cli extract huge1.pdf huge2.pdf small.pdf --timeout 120 -o ./out/
Batch: 3 files
[1/3] Done: small.pdf -> ./out/small.md (5.2 KB, 8.1s)
Timeout: batch exceeded 120s limit
Result: 1/3 succeeded, 2 timed out (120.0s)
```

---

## 9. 构建与分发

### 9.1 目标平台

| GOOS | GOARCH | 产物名 |
|------|--------|--------|
| linux | amd64 | `mineru-open-api-cli-linux-amd64` |
| linux | arm64 | `mineru-open-api-cli-linux-arm64` |
| darwin | amd64 | `mineru-open-api-cli-darwin-amd64` |
| darwin | arm64 | `mineru-open-api-cli-darwin-arm64` |
| windows | amd64 | `mineru-open-api-cli-windows-amd64.exe` |
| windows | arm64 | `mineru-open-api-cli-windows-arm64.exe` |

### 9.2 goreleaser 配置要点

```yaml
# .goreleaser.yaml
project_name: mineru-open-api-cli
builds:
  - main: ./main.go
    binary: mineru-open-api-cli
    goos: [linux, darwin, windows]
    goarch: [amd64, arm64]
    ldflags:
      - -s -w
      - -X main.version={{.Version}}
      - -X main.commit={{.ShortCommit}}
      - -X main.date={{.Date}}

archives:
  - format: tar.gz
    name_template: "{{ .ProjectName }}-{{ .Os }}-{{ .Arch }}"
    format_overrides:
      - goos: windows
        format: zip

brews:
  - repository:
      owner: OpenDataLab
      name: homebrew-tap
    homepage: https://mineru.net
    description: "MinerU Open API CLI — turn documents into Markdown"

changelog:
  sort: asc
```

### 9.3 分发渠道

| 渠道 | 用户操作 | 覆盖 |
|------|---------|------|
| **GitHub Releases** | 下载 tar.gz / zip 解压 | 所有平台 |
| **install.sh** | `curl -sSL https://mineru.net/install.sh \| sh` | macOS / Linux |
| **Homebrew** | `brew install opendatalab/tap/mineru-open-api-cli` | macOS / Linux |
| **Scoop** | `scoop bucket add mineru-open-api-cli ...; scoop install mineru-open-api-cli` | Windows |
| **Docker** | `docker run mineru-open-api-cli extract ...` | 全平台 |

### 9.4 install.sh 逻辑

```
1. 检测 OS + ARCH
2. 从 GitHub Releases 下载对应二进制
3. 放到 /usr/local/bin/mineru-open-api-cli
4. chmod +x
5. 打印 "mineru-open-api-cli installed, run: mineru-open-api-cli version"
```

---

## 10. 版本号注入

编译时通过 ldflags 注入，不硬编码：

```go
// main.go
var (
    version = "dev"
    commit  = "none"
    date    = "unknown"
)
```

```bash
$ mineru-open-api-cli version
mineru-open-api-cli v0.1.0 (commit: a1b2c3d, built: 2026-03-15)
```

---

## 11. 实现阶段

### Phase 1: 能跑（1-2 天）

- [ ] 项目初始化：go mod、cobra 脚手架
- [ ] `extract` 命令：单文件 stdout 模式跑通（token → SDK → markdown 输出到 stdout）
- [ ] `extract` 命令：单文件 -o 模式（保存到文件）
- [ ] `-f` 格式选择 + 不合法组合的错误提示
- [ ] `auth` 命令：交互式保存 token
- [ ] `version` 命令
- [ ] 基本错误处理 + 退出码

### Phase 2: 好用（2-3 天）

- [ ] `extract` 批量模式（多参数 + --list + --stdin-list + 自己轮询进度）
- [ ] `crawl` 命令（单个 + 批量，复用 extract 的逻辑）
- [ ] `status` 命令
- [ ] `--stdin" 输入模式
- [ ] 批量超时（总超时语义）

### Phase 3: 能发（1-2 天）

- [ ] goreleaser 配置
- [ ] GitHub Actions 自动发布
- [ ] install.sh 安装脚本
- [ ] shell completion（bash/zsh/fish/powershell）
- [ ] README 编写

### Phase 4: 锦上添花（后续迭代）

- [ ] Homebrew / Scoop 包管理器集成
- [ ] Docker 镜像
- [ ] `mineru-open-api-cli config` 子命令（管理 base_url 等高级配置）
- [ ] 自动更新检查（`mineru-open-api-cli update`）

---

## 12. 与 SDK 的依赖关系

```
mineru-open-api-cli 的 go.mod:

module github.com/OpenDataLab/mineru-open-api-cli

require github.com/OpenDataLab/mineru-open-sdk-go v0.1.0

// 开发期间用 replace 指向本地：
// replace github.com/OpenDataLab/mineru-open-sdk-go => ../mineru-open-sdk-go
```

**内网开发期间**，module 路径改为内网地址（与 SDK 发布计划一致）。正式发布前改回 GitHub 路径。

---

## 13. 命名

| 维度 | 值 |
|------|----|
| 二进制名 | `mineru-open-api-cli` |
| Go module | `github.com/OpenDataLab/mineru-open-api-cli` |
| GitHub 仓库 | `OpenDataLab/mineru-open-api-cli` |
| Homebrew formula | `mineru-open-api-cli` |
| PyPI 无关 | CLI 是独立发布，和 Python SDK 无关联 |

用户只需要记住一个词：`mineru-open-api-cli`。

---

## 附录 A: 设计决策记录

| # | 决策 | 理由 |
|---|------|------|
| D1 | 去掉 `batch` 命令，extract/crawl 自带批量 | 少一个命令少一个概念，用户不需要多记一个词 |
| D2 | 默认无美化（无 spinner/颜色/ANSI） | 2026 年最大调用方是 AI Agent，TTY 检测区分不了人和 Agent |
| D3 | 砍掉 `--json`/`-q`/`--no-color`/`--stdout` | 默认输出已经对 Agent 和人都友好，减少概念 and 维护成本 |
| D4 | `-o` 决定输出模式（curl 风格） | 无 -o 内容到 stdout，有 -o 存文件；一个 flag 控制一切 |
| D5 | `-f` 在 stdout 模式下支持单个文本格式 | Agent 可能需要 html/json/latex，不只是 markdown |
| D6 | CLI 自己轮询，不用 SDK 的 ExtractBatch | SDK channel 吞掉 running 状态的中间进度，CLI 需要展示 |
| D7 | 批量 --timeout 是总超时 | SubmitBatch 一把提交，per-file 超时实现不了也不符合直觉 |
