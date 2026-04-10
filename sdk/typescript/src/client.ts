import { readFile } from "node:fs/promises";
import { basename, extname } from "node:path";

import { ApiClient } from "./api.js";
import { DEFAULT_BASE_URL } from "./constants.js";
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

/** Default total business timeouts for extraction tasks (in seconds). */
const DEFAULT_TIMEOUT_POLL_SINGLE = 300;
const DEFAULT_TIMEOUT_POLL_BATCH = 1800;

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
  model?: string;
  ocr?: boolean;
  formula?: boolean;
  table?: boolean;
  language?: string;
  pages?: string;
  extraFormats?: string[];
  /** Per-file overrides keyed by path or URL. */
  fileParams?: Record<string, FileParam>;
  /** Max total seconds to wait for task completion (polling). */
  timeout?: number;
}

export interface BatchOptions {
  model?: string;
  ocr?: boolean;
  formula?: boolean;
  table?: boolean;
  language?: string;
  extraFormats?: string[];
  /** Per-file overrides keyed by path or URL. */
  fileParams?: Record<string, FileParam>;
  /** Max total seconds to wait for all tasks (polling). */
  timeout?: number;
}

export interface FlashExtractOptions {
  language?: string;
  pageRange?: string;
  ocr?: boolean;
  formula?: boolean;
  table?: boolean;
  /** Max total seconds to wait for task completion (polling). */
  timeout?: number;
}

/** Per-file parameter overrides for batch methods. */
export interface FileParam {
  /** Override page_ranges for this file (e.g. "1-10,15"). */
  pages?: string;
  /** Override is_ocr for this file. */
  ocr?: boolean;
  /** Set data_id for this file. */
  dataId?: string;
}

/** Only includes fields the user explicitly set. Never assumes API defaults. */
function buildApiOptions(
  modelVersion: string,
  opts: ExtractOptions | BatchOptions,
): Record<string, unknown> {
  const o: Record<string, unknown> = { model_version: modelVersion };
  if (opts.formula !== undefined) o["enable_formula"] = opts.formula;
  if (opts.table !== undefined) o["enable_table"] = opts.table;
  if (opts.language !== undefined) o["language"] = opts.language;
  if (opts.extraFormats?.length) {
    o["extra_formats"] = opts.extraFormats;
  }
  return o;
}

/** Adds per-file fields (is_ocr, page_ranges, data_id) to a file entry. */
function applyFileFields(
  entry: Record<string, unknown>,
  key: string,
  ocr: boolean | undefined,
  pages: string | undefined,
  fileParams: Record<string, FileParam> | undefined,
): void {
  const fp = fileParams?.[key];

  // OCR: per-file overrides global
  const effectiveOcr = fp?.ocr !== undefined ? fp.ocr : ocr;
  if (effectiveOcr !== undefined) entry["is_ocr"] = effectiveOcr;

  // Pages: per-file overrides global
  const effectivePages = fp?.pages || pages;
  if (effectivePages) entry["page_ranges"] = effectivePages;

  // DataID: per-file only
  if (fp?.dataId) entry["data_id"] = fp.dataId;
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
 */
export class MinerU {
  private readonly api: ApiClient | null;
  private readonly flashApi: FlashApiClient;

  /**
   * @param token - API token.
   * @param baseUrl - API base URL.
   * @param flashBaseUrl - Flash API base URL.
   */
  constructor(
    token?: string,
    baseUrl = DEFAULT_BASE_URL,
    flashBaseUrl?: string,
  ) {
    const resolved = token ?? process.env["MINERU_TOKEN"];
    if (resolved) {
      // ApiClient should ideally use DEFAULT_TIMEOUT_REQUEST internally
      this.api = new ApiClient(resolved, baseUrl, DEFAULT_SOURCE);
    } else {
      this.api = null; // flash-only mode
    }
    this.flashApi = new FlashApiClient(flashBaseUrl, DEFAULT_SOURCE);
  }

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

  async extract(
    source: string,
    options: ExtractOptions = {},
  ): Promise<ExtractResult> {
    this.requireAuth();
    const { timeout = DEFAULT_TIMEOUT_POLL_SINGLE, ...opts } = options;
    const modelVersion = resolveModel(opts.model, source);
    const apiOpts = buildApiOptions(modelVersion, opts);

    let batchId: string;
    if (isUrl(source)) {
      batchId = await this.submitUrlsBatch([source], apiOpts, opts.ocr, opts.pages, opts.fileParams);
    } else {
      batchId = await this.uploadAndSubmit([source], apiOpts, opts.ocr, opts.pages, opts.fileParams);
    }
    const results = await this.waitBatch(batchId, timeout);
    return results[0]!;
  }

  async *extractBatch(
    sources: string[],
    options: BatchOptions = {},
  ): AsyncGenerator<ExtractResult> {
    this.requireAuth();
    const { timeout = DEFAULT_TIMEOUT_POLL_BATCH, ...opts } = options;
    const firstSource = sources[0] ?? "";
    const modelVersion = resolveModel(opts.model, firstSource);
    const apiOpts = buildApiOptions(modelVersion, opts);

    const urls = sources.filter(isUrl);
    const files = sources.filter((s) => !isUrl(s));

    const batchIds: string[] = [];
    if (urls.length > 0) {
      batchIds.push(await this.submitUrlsBatch(urls, apiOpts, opts.ocr, undefined, opts.fileParams));
    }
    if (files.length > 0) {
      batchIds.push(await this.uploadAndSubmit(files, apiOpts, opts.ocr, undefined, opts.fileParams));
    }

    yield* this.yieldBatch(batchIds, sources.length, timeout);
  }

  async crawl(
    url: string,
    options: { extraFormats?: string[]; timeout?: number } = {},
  ): Promise<ExtractResult> {
    return this.extract(url, { model: "html", timeout: DEFAULT_TIMEOUT_POLL_SINGLE, ...options });
  }

  async *crawlBatch(
    urls: string[],
    options: { extraFormats?: string[]; timeout?: number } = {},
  ): AsyncGenerator<ExtractResult> {
    yield* this.extractBatch(urls, { model: "html", timeout: DEFAULT_TIMEOUT_POLL_BATCH, ...options });
  }

  // ══════════════════════════════════════════════════════════════════
  //  Async primitives (no polling, no waiting)
  // ══════════════════════════════════════════════════════════════════

  async submit(
    source: string,
    options: Omit<ExtractOptions, "timeout"> = {},
  ): Promise<string> {
    this.requireAuth();
    const modelVersion = resolveModel(options.model, source);
    const apiOpts = buildApiOptions(modelVersion, options);

    if (isUrl(source)) {
      return this.submitUrlsBatch([source], apiOpts, options.ocr, options.pages, options.fileParams);
    }
    return this.uploadAndSubmit([source], apiOpts, options.ocr, options.pages, options.fileParams);
  }

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
      return this.submitUrlsBatch(urls, apiOpts, options.ocr, undefined, options.fileParams);
    }
    return this.uploadAndSubmit(files, apiOpts, options.ocr, undefined, options.fileParams);
  }

  async getTask(taskId: string): Promise<ExtractResult> {
    const api = this.requireAuth();
    const body = await api.get(`/extract/task/${taskId}`);
    const result = parseTaskResult(body.data);
    if (result.state === "done" && result.zipUrl) {
      return this.downloadAndParse(result);
    }
    return result;
  }

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

  private async submitUrlsBatch(
    urls: string[],
    opts: Record<string, unknown>,
    ocr: boolean | undefined,
    pages: string | undefined,
    fileParams: Record<string, FileParam> | undefined,
  ): Promise<string> {
    const files = urls.map((u) => {
      const entry: Record<string, unknown> = { url: u };
      applyFileFields(entry, u, ocr, pages, fileParams);
      return entry;
    });
    const body = await this.requireAuth().post("/extract/task/batch", {
      files,
      ...opts,
    });
    return body.data["batch_id"] as string;
  }

  private async uploadAndSubmit(
    filePaths: string[],
    opts: Record<string, unknown>,
    ocr: boolean | undefined,
    pages: string | undefined,
    fileParams: Record<string, FileParam> | undefined,
  ): Promise<string> {
    const api = this.requireAuth();
    const filesMeta = filePaths.map((p) => {
      const entry: Record<string, unknown> = { name: basename(p) };
      applyFileFields(entry, p, ocr, pages, fileParams);
      return entry;
    });
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

  async flashExtract(
    source: string,
    options: FlashExtractOptions = {},
  ): Promise<ExtractResult> {
    const { language = "ch", pageRange, ocr, formula, table, timeout = DEFAULT_TIMEOUT_POLL_SINGLE } = options;

    let taskId: string;
    if (isUrl(source)) {
      taskId = await this.flashSubmitUrl(source, language, pageRange, ocr, formula, table);
    } else {
      taskId = await this.flashSubmitFile(source, language, pageRange, ocr, formula, table);
    }

    return this.flashWait(taskId, timeout);
  }

  // ── Flash internal helpers ──

  private async flashSubmitUrl(
    url: string,
    language: string,
    pageRange?: string,
    ocr?: boolean,
    formula?: boolean,
    table?: boolean,
  ): Promise<string> {
    const payload: Record<string, unknown> = { url, language };
    if (pageRange != null) payload["page_range"] = pageRange;
    if (ocr != null) payload["is_ocr"] = ocr;
    if (formula != null) payload["enable_formula"] = formula;
    if (table != null) payload["enable_table"] = table;
    const body = await this.flashApi.post("/parse/url", payload);
    return body.data["task_id"] as string;
  }

  private async flashSubmitFile(
    filePath: string,
    language: string,
    pageRange?: string,
    ocr?: boolean,
    formula?: boolean,
    table?: boolean,
  ): Promise<string> {
    const fileName = basename(filePath);
    const payload: Record<string, unknown> = { file_name: fileName, language };
    if (pageRange != null) payload["page_range"] = pageRange;
    if (ocr != null) payload["is_ocr"] = ocr;
    if (formula != null) payload["enable_formula"] = formula;
    if (table != null) payload["enable_table"] = table;
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
