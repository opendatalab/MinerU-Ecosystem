import { writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";

export interface Image {
  name: string;
  data: Uint8Array;
  path: string;
}

export interface Progress {
  extractedPages: number;
  totalPages: number;
  startTime: string;
}

export function progressPercent(p: Progress): number {
  if (p.totalPages === 0) return 0;
  return (p.extractedPages / p.totalPages) * 100;
}

export function progressToString(p: Progress): string {
  return `${p.extractedPages}/${p.totalPages} (${progressPercent(p).toFixed(0)}%)`;
}

export interface ExtractResult {
  taskId: string;
  state: string;
  filename: string | null;
  error: string | null;
  zipUrl: string | null;

  progress: Progress | null;

  markdown: string | null;
  contentList: Record<string, unknown>[] | null;
  images: Image[];

  docx: Uint8Array | null;
  html: string | null;
  latex: string | null;

  /** @internal */
  _zipBytes: Uint8Array | null;
}

export function createEmptyResult(
  taskId: string,
  state: string,
): ExtractResult {
  return {
    taskId,
    state,
    filename: null,
    error: null,
    zipUrl: null,
    progress: null,
    markdown: null,
    contentList: null,
    images: [],
    docx: null,
    html: null,
    latex: null,
    _zipBytes: null,
  };
}

async function ensureDir(filePath: string): Promise<void> {
  await mkdir(dirname(filePath), { recursive: true });
}

export async function saveMarkdown(
  result: ExtractResult,
  path: string,
  withImages = true,
): Promise<void> {
  if (result.markdown == null) {
    throw new Error("No markdown content available (state != done)");
  }
  await ensureDir(path);
  await writeFile(path, result.markdown, "utf-8");
  if (withImages && result.images.length > 0) {
    const imgDir = join(dirname(path), "images");
    await mkdir(imgDir, { recursive: true });
    for (const img of result.images) {
      await writeFile(join(imgDir, img.name), img.data);
    }
  }
}

export async function saveDocx(
  result: ExtractResult,
  path: string,
): Promise<void> {
  if (result.docx == null) {
    throw new Error(
      "No docx content — did you pass extraFormats: ['docx']?",
    );
  }
  await ensureDir(path);
  await writeFile(path, result.docx);
}

export async function saveHtml(
  result: ExtractResult,
  path: string,
): Promise<void> {
  if (result.html == null) {
    throw new Error(
      "No html content — did you pass extraFormats: ['html']?",
    );
  }
  await ensureDir(path);
  await writeFile(path, result.html, "utf-8");
}

export async function saveLatex(
  result: ExtractResult,
  path: string,
): Promise<void> {
  if (result.latex == null) {
    throw new Error(
      "No latex content — did you pass extraFormats: ['latex']?",
    );
  }
  await ensureDir(path);
  await writeFile(path, result.latex, "utf-8");
}

export async function saveAll(
  result: ExtractResult,
  dir: string,
): Promise<void> {
  if (result._zipBytes == null) {
    throw new Error("No zip data available (state != done)");
  }
  const { unzipSync } = await import("fflate");
  const entries = unzipSync(new Uint8Array(result._zipBytes));
  await mkdir(dir, { recursive: true });
  for (const [relativePath, content] of Object.entries(entries)) {
    if (relativePath.endsWith("/")) continue;
    const fullPath = join(dir, relativePath);
    await ensureDir(fullPath);
    await writeFile(fullPath, content);
  }
}
