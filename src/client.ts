import { readFile } from "node:fs/promises";
import { basename, extname } from "node:path";

import { ApiClient } from "./api.js";
import { NoAuthClientError, TimeoutError } from "./errors.js";
import { FlashApiClient } from "./flash-api.js";
import type { ExtractResult, Progress } from "./models.js";
import { createEmptyResult } from "./models.js";
import { parseZip } from "./zip.js";

const MODEL_MAP: Record<string, string> = {
  pipeline: "pipeline",
  vlm: "vlm",
  html: "MinerU-HTML",
};

const HTML_EXTENSIONS = new Set([".html", ".htm"]);

const DEFAULT_SOURCE = "open-api-sdk-js";

function isUrl(source: string): boolean {
  return source.startsWith("http://") || source.startsWith("https://");
}

function getExtension(source: string): string {
  if (isUrl(source)) {
    const path = source.split("?")[0]!.split("#")[0]!;
    const dot = path.lastIndexOf(".");
    return dot === -1 ? "" : path.slice(dot).toLowerCase();
  }
  return extname(source).toLowerCase();
}

function inferModel(source: string): string {
  return HTML_EXTENSIONS.has(getExtension(source)) ? "MinerU-HTML" : "vlm";
}

function resolveModel(model: string | undefined, source: string): string {
  if (model != null) {
    return MODEL_MAP[model] ?? model;
  }
  return inferModel(source);
}

export interface ExtractOptions {
  /** `"pipeline"` | `"vlm"` | `"html"`. Auto-inferred if omitted. */
  model?: string;
  /** Enable OCR. Only effective with pipeline or vlm models. */
  ocr?: boolean;
  /** Enable formula recognition. Default: true. */
  formula?: boolean;
  /** Enable table recognition. Default: true. */
  table?: boolean;
  /** Document language code. Default: `"ch"`. */
  language?: string;
  /** Page range string, e.g. `"1-10,15"` or `"2--2"`. */
  pages?: string;
  /** Additional export formats: `"docx"`, `"html"`, `"latex"`. */
  extraFormats?: string[];
  /** Max seconds to wait for completion. Default: 300. */
  timeout?: number;
}

export interface BatchOptions {
  model?: string;
  ocr?: boolean;
  formula?: boolean;
  table?: boolean;
  language?: string;
  extraFormats?: string[];
  timeout?: number;
}

export interface FlashExtractOptions {
  /** Document language code. Default: `"ch"`. */
  language?: string;
  /** Page range, e.g. `"1-10"`. */
  pageRange?: string;
  /** Max seconds to wait. Default: 300. */
  timeout?: number;
}

function buildApiOptions(
  modelVersion: string,
  opts: ExtractOptions | BatchOptions,
): Record<string, unknown> {
  const o: Record<string, unknown> = { model_version: modelVersion };
  if (opts.ocr) o["is_ocr"] = true;
  if (opts.formula === false) o["enable_formula"] = false;
  if (opts.table === false) o["enable_table"] = false;
  if (opts.language != null && opts.language !== "ch") {
    o["language"] = opts.language;
  }
  if ("pages" in opts && opts.pages != null) {
    o["page_ranges"] = opts.pages;
  }
  if (opts.extraFormats?.length) {
    o["extra_formats"] = opts.extraFormats;
  }
  return o;
}

function parseTaskResult(data: Record<string, unknown>): ExtractResult {
  const result = createEmptyResult(
    (data["task_id"] as string) ?? "",
    (data["state"] as string) ?? "unknown",
  );
  result.filename = (data["file_name"] as string) ?? null;
  const errCodeRaw = data["err_code"];
  result.errCode = errCodeRaw == null ? "" : String(errCodeRaw);
  result.error = (data["err_msg"] as string) || null;
  result.zipUrl = (data["full_zip_url"] as string) ?? null;

  const ep = data["extract_progress"] as Record<string, unknown> | undefined;
  if (ep) {
    result.progress = {
      extractedPages: (ep["extracted_pages"] as number) ?? 0,
      totalPages: (ep["total_pages"] as number) ?? 0,
      startTime: (ep["start_time"] as string) ?? "",
    } satisfies Progress;
  }
  return result;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * MinerU API client. Turn documents into Markdown with one method call.
 *
 * When no token is provided and `MINERU_TOKEN` is not set, a flash-only
 * client is created. Only {@link flashExtract} is available; calling
 * standard methods throws {@link NoAuthClientError}.
 *
 * @example
 * ```ts
 * import { MinerU } from "mineru";
 *
 * const client = new MinerU(); // reads MINERU_TOKEN env var
 * const md = (await client.extract("https://example.com/doc.pdf")).markdown;
 * ```
 */
export class MinerU {
  private readonly api: ApiClient | null;
  private readonly flashApi: FlashApiClient;

  /**
   * @param token - API token. If omitted, reads `MINERU_TOKEN` env var.
   *   If neither is available, creates a flash-only client.
   * @param baseUrl - API base URL. Override for private deployments.
   * @param flashBaseUrl - Flash API base URL. Override for testing.
   */
  constructor(
    token?: string,
    baseUrl = "https://mineru.net/api/v4",
    flashBaseUrl?: string,
  ) {
    const resolved = token ?? process.env["MINERU_TOKEN"];
    if (resolved) {
      this.api = new ApiClient(resolved, baseUrl, DEFAULT_SOURCE);
    } else {
      this.api = null; // flash-only mode
    }
    this.flashApi = new FlashApiClient(flashBaseUrl, DEFAULT_SOURCE);
  }

  /**
   * Override the source identifier sent with API requests.
   * Used to track which application or integration is making the call.
   */
  setSource(source: string): void {
    if (this.api !== null) {
      this.api.setSource(source);
    }
    this.flashApi.setSource(source);
  }

  private requireAuth(): ApiClient {
    if (this.api === null) {
      throw new NoAuthClientError();
    }
    return this.api;
  }

  // ══════════════════════════════════════════════════════════════════
  //  Synchronous (blocking) methods
  // ══════════════════════════════════════════════════════════════════

  /**
   * Parse a single document. Blocks until the result is ready.
   *
   * @example
   * ```ts
   * const result = await new MinerU().extract("https://example.com/doc.pdf");
   * console.log(result.markdown);
   * ```
   */
  async extract(
    source: string,
    options: ExtractOptions = {},
  ): Promise<ExtractResult> {
    this.requireAuth();
    const { timeout = 300, ...opts } = options;
    const modelVersion = resolveModel(opts.model, source);
    const apiOpts = buildApiOptions(modelVersion, opts);

    if (isUrl(source)) {
      const taskId = await this.submitUrl(source, apiOpts);
      return this.waitSingle(taskId, timeout);
    }
    const batchId = await this.uploadAndSubmit([source], apiOpts);
    const results = await this.waitBatch(batchId, timeout);
    return results[0]!;
  }

  /**
   * Parse multiple documents. Returns an async iterable that yields
   * each result as it completes — first done, first yielded.
   *
   * @example
   * ```ts
   * for await (const r of client.extractBatch(["a.pdf", "b.pdf"])) {
   *   console.log(r.markdown);
   * }
   * ```
   */
  async *extractBatch(
    sources: string[],
    options: BatchOptions = {},
  ): AsyncGenerator<ExtractResult> {
    this.requireAuth();
    const { timeout = 600, ...opts } = options;
    const firstSource = sources[0] ?? "";
    const modelVersion = resolveModel(opts.model, firstSource);
    const apiOpts = buildApiOptions(modelVersion, opts);

    const urls = sources.filter(isUrl);
    const files = sources.filter((s) => !isUrl(s));

    const batchIds: string[] = [];
    if (urls.length > 0) {
      batchIds.push(await this.submitUrlsBatch(urls, apiOpts));
    }
    if (files.length > 0) {
      batchIds.push(await this.uploadAndSubmit(files, apiOpts));
    }

    yield* this.yieldBatch(batchIds, sources.length, timeout);
  }

  /**
   * Crawl a web page and parse it to Markdown.
   * Shorthand for `extract(url, { model: "html" })`.
   */
  async crawl(
    url: string,
    options: { extraFormats?: string[]; timeout?: number } = {},
  ): Promise<ExtractResult> {
    return this.extract(url, { model: "html", ...options });
  }

  /**
   * Crawl multiple web pages. Yields results as each completes.
   * Shorthand for `extractBatch(urls, { model: "html" })`.
   */
  async *crawlBatch(
    urls: string[],
    options: { extraFormats?: string[]; timeout?: number } = {},
  ): AsyncGenerator<ExtractResult> {
    yield* this.extractBatch(urls, { model: "html", ...options });
  }

  // ══════════════════════════════════════════════════════════════════
  //  Async primitives (no polling, no waiting)
  // ══════════════════════════════════════════════════════════════════

  /**
   * Submit a single task without waiting. Returns a task ID (for URLs)
   * or batch ID (for local files).
   *
   * Use {@link getTask} later to check the result.
   */
  async submit(
    source: string,
    options: Omit<ExtractOptions, "timeout"> = {},
  ): Promise<string> {
    this.requireAuth();
    const modelVersion = resolveModel(options.model, source);
    const apiOpts = buildApiOptions(modelVersion, options);

    if (isUrl(source)) {
      return this.submitUrl(source, apiOpts);
    }
    return this.uploadAndSubmit([source], apiOpts);
  }

  /**
   * Submit multiple tasks without waiting. Returns a batch ID.
   *
   * Use {@link getBatch} later to check results.
   */
  async submitBatch(
    sources: string[],
    options: Omit<BatchOptions, "timeout"> = {},
  ): Promise<string> {
    this.requireAuth();
    const firstSource = sources[0] ?? "";
    const modelVersion = resolveModel(options.model, firstSource);
    const apiOpts = buildApiOptions(modelVersion, options);

    const urls = sources.filter(isUrl);
    const files = sources.filter((s) => !isUrl(s));

    if (urls.length === 0 && files.length === 0) {
      throw new Error("No sources provided.");
    }
    if (urls.length > 0 && files.length > 0) {
      throw new Error(
        "submitBatch() does not support mixing URLs and local files in one call. " +
          "Please submit them separately or use extractBatch() instead.",
      );
    }

    if (urls.length > 0) {
      return this.submitUrlsBatch(urls, apiOpts);
    }
    return this.uploadAndSubmit(files, apiOpts);
  }

  /**
   * Query a single task's current state. When `state === "done"`,
   * the result zip is downloaded and parsed automatically.
   */
  async getTask(taskId: string): Promise<ExtractResult> {
    const api = this.requireAuth();
    const body = await api.get(`/extract/task/${taskId}`);
    const result = parseTaskResult(body.data);
    if (result.state === "done" && result.zipUrl) {
      return this.downloadAndParse(result);
    }
    return result;
  }

  /**
   * Query all tasks in a batch. Completed tasks have their content
   * populated; in-progress tasks have `markdown === null`.
   */
  async getBatch(batchId: string): Promise<ExtractResult[]> {
    const api = this.requireAuth();
    const body = await api.get(`/extract-results/batch/${batchId}`);
    const items = (body.data["extract_result"] as Record<string, unknown>[]) ?? [];
    const results: ExtractResult[] = [];
    for (const item of items) {
      let r = parseTaskResult(item);
      if (r.state === "done" && r.zipUrl) {
        r = await this.downloadAndParse(r);
      }
      results.push(r);
    }
    return results;
  }

  // ══════════════════════════════════════════════════════════════════
  //  Internal helpers
  // ══════════════════════════════════════════════════════════════════

  private async submitUrl(
    url: string,
    opts: Record<string, unknown>,
  ): Promise<string> {
    const body = await this.requireAuth().post("/extract/task", { url, ...opts });
    return body.data["task_id"] as string;
  }

  private async submitUrlsBatch(
    urls: string[],
    opts: Record<string, unknown>,
  ): Promise<string> {
    const files = urls.map((u) => ({ url: u }));
    const body = await this.requireAuth().post("/extract/task/batch", {
      files,
      ...opts,
    });
    return body.data["batch_id"] as string;
  }

  private async uploadAndSubmit(
    filePaths: string[],
    opts: Record<string, unknown>,
  ): Promise<string> {
    const api = this.requireAuth();
    const filesMeta = filePaths.map((p) => ({ name: basename(p) }));
    const body = await api.post("/file-urls/batch", {
      files: filesMeta,
      ...opts,
    });
    const batchId = body.data["batch_id"] as string;
    const uploadUrls = body.data["file_urls"] as string[];

    for (let i = 0; i < filePaths.length; i++) {
      const data = await readFile(filePaths[i]!);
      await api.putFile(uploadUrls[i]!, new Uint8Array(data));
    }

    return batchId;
  }

  private async downloadAndParse(
    result: ExtractResult,
  ): Promise<ExtractResult> {
    const zipBytes = await this.requireAuth().download(result.zipUrl!);
    const parsed = parseZip(zipBytes, result.taskId, result.filename);
    parsed.zipUrl = result.zipUrl;
    return parsed;
  }

  private async waitSingle(
    taskId: string,
    timeout: number,
  ): Promise<ExtractResult> {
    const deadline = Date.now() + timeout * 1000;
    let interval = 2000;
    for (;;) {
      const result = await this.getTask(taskId);
      if (result.state === "done" || result.state === "failed") {
        return result;
      }
      if (Date.now() > deadline) {
        throw new TimeoutError(timeout, taskId);
      }
      await sleep(Math.min(interval, Math.max(0, deadline - Date.now())));
      interval = Math.min(interval * 2, 30_000);
    }
  }

  private async waitBatch(
    batchId: string,
    timeout: number,
  ): Promise<ExtractResult[]> {
    const deadline = Date.now() + timeout * 1000;
    let interval = 2000;
    for (;;) {
      const results = await this.getBatch(batchId);
      if (results.every((r) => r.state === "done" || r.state === "failed")) {
        return results;
      }
      if (Date.now() > deadline) {
        throw new TimeoutError(timeout, batchId);
      }
      await sleep(Math.min(interval, Math.max(0, deadline - Date.now())));
      interval = Math.min(interval * 2, 30_000);
    }
  }

  private async *yieldBatch(
    batchIds: string[],
    total: number,
    timeout: number,
  ): AsyncGenerator<ExtractResult> {
    const deadline = Date.now() + timeout * 1000;
    const yielded = new Set<string>();
    let interval = 2000;

    while (yielded.size < total) {
      for (const bid of batchIds) {
        const results = await this.getBatch(bid);
        for (let idx = 0; idx < results.length; idx++) {
          const key = `${bid}:${idx}`;
          const r = results[idx]!;
          if (!yielded.has(key) && (r.state === "done" || r.state === "failed")) {
            yielded.add(key);
            yield r;
          }
        }
      }

      if (yielded.size >= total) break;
      if (Date.now() > deadline) {
        throw new TimeoutError(timeout, batchIds.join(","));
      }
      await sleep(Math.min(interval, Math.max(0, deadline - Date.now())));
      interval = Math.min(interval * 2, 30_000);
    }
  }

  // ══════════════════════════════════════════════════════════════════
  //  Flash (agent) mode
  // ══════════════════════════════════════════════════════════════════

  /**
   * Parse a document using the flash (agent) API.
   * No token required. Only outputs Markdown.
   *
   * @example
   * ```ts
   * const client = new MinerU(); // no token needed for flash mode
   * const result = await client.flashExtract("report.pdf");
   * console.log(result.markdown);
   * ```
   */
  async flashExtract(
    source: string,
    options: FlashExtractOptions = {},
  ): Promise<ExtractResult> {
    const { language = "ch", pageRange, timeout = 300 } = options;

    let taskId: string;
    if (isUrl(source)) {
      taskId = await this.flashSubmitUrl(source, language, pageRange);
    } else {
      taskId = await this.flashSubmitFile(source, language, pageRange);
    }

    return this.flashWait(taskId, timeout);
  }

  // ── Flash internal helpers ──

  private async flashSubmitUrl(
    url: string,
    language: string,
    pageRange?: string,
  ): Promise<string> {
    const payload: Record<string, unknown> = { url, language };
    if (pageRange != null) payload["page_range"] = pageRange;
    const body = await this.flashApi.post("/parse/url", payload);
    return body.data["task_id"] as string;
  }

  private async flashSubmitFile(
    filePath: string,
    language: string,
    pageRange?: string,
  ): Promise<string> {
    const fileName = basename(filePath);
    const payload: Record<string, unknown> = { file_name: fileName, language };
    if (pageRange != null) payload["page_range"] = pageRange;
    const body = await this.flashApi.post("/parse/file", payload);
    const taskId = body.data["task_id"] as string;
    const fileUrl = body.data["file_url"] as string;

    const data = await readFile(filePath);
    await this.flashApi.putFile(fileUrl, new Uint8Array(data));
    return taskId;
  }

  private async flashWait(
    taskId: string,
    timeout: number,
  ): Promise<ExtractResult> {
    const deadline = Date.now() + timeout * 1000;
    let interval = 2000;
    for (;;) {
      const result = await this.flashGetTask(taskId);
      if (result.state === "done" || result.state === "failed") return result;
      if (Date.now() > deadline) throw new TimeoutError(timeout, taskId);
      await sleep(Math.min(interval, Math.max(0, deadline - Date.now())));
      interval = Math.min(interval * 2, 30_000);
    }
  }

  private async flashGetTask(taskId: string): Promise<ExtractResult> {
    const body = await this.flashApi.get(`/parse/${taskId}`);
    return this.parseFlashTask(body.data);
  }

  private async parseFlashTask(
    data: Record<string, unknown>,
  ): Promise<ExtractResult> {
    const result = createEmptyResult(
      (data["task_id"] as string) ?? "",
      (data["state"] as string) ?? "unknown",
    );
    const errCodeRaw = data["err_code"];
    result.errCode = errCodeRaw == null ? "" : String(errCodeRaw);
    result.error = (data["err_msg"] as string) || null;

    const ep = data["extract_progress"] as
      | Record<string, unknown>
      | undefined;
    if (ep) {
      result.progress = {
        extractedPages: (ep["extracted_pages"] as number) ?? 0,
        totalPages: (ep["total_pages"] as number) ?? 0,
        startTime: (ep["start_time"] as string) ?? "",
      };
    }

    if (result.state === "done" && data["markdown_url"]) {
      result.markdown = await this.flashApi.downloadText(
        data["markdown_url"] as string,
      );
    }

    return result;
  }
}
