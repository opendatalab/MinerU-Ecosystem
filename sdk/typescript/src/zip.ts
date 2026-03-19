import { unzipSync } from "fflate";
import type { ExtractResult, Image } from "./models.js";
import { createEmptyResult } from "./models.js";

const IMAGE_EXTENSIONS = new Set([
  ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
]);

function extname(filename: string): string {
  const dot = filename.lastIndexOf(".");
  return dot === -1 ? "" : filename.slice(dot).toLowerCase();
}

function basename(filepath: string): string {
  const parts = filepath.replace(/\\/g, "/").split("/");
  return parts[parts.length - 1] ?? "";
}

export function parseZip(
  zipBytes: Uint8Array,
  taskId: string,
  filename: string | null = null,
): ExtractResult {
  const result = createEmptyResult(taskId, "done");
  result.filename = filename;
  result._zipBytes = zipBytes;

  const entries = unzipSync(zipBytes);
  const images: Image[] = [];
  let contentList: Record<string, unknown>[] | null = null;

  for (const [relPath, data] of Object.entries(entries)) {
    if (relPath.endsWith("/")) continue;

    const name = basename(relPath);
    const ext = extname(name);
    const text = () => new TextDecoder().decode(data);

    if (ext === ".md") {
      result.markdown = text();
    } else if (
      name.endsWith("_content_list.json") ||
      name === "content_list.json"
    ) {
      contentList = JSON.parse(text()) as Record<string, unknown>[];
    } else if (ext === ".json" && contentList == null) {
      try {
        const parsed: unknown = JSON.parse(text());
        if (Array.isArray(parsed)) {
          contentList = parsed as Record<string, unknown>[];
        }
      } catch {
        // not a valid JSON array — skip
      }
    } else if (IMAGE_EXTENSIONS.has(ext)) {
      images.push({ name, data: new Uint8Array(data), path: relPath });
    } else if (ext === ".docx") {
      result.docx = new Uint8Array(data);
    } else if (ext === ".html" || ext === ".htm") {
      result.html = text();
    } else if (ext === ".tex") {
      result.latex = text();
    }
  }

  result.contentList = contentList;
  result.images = images;
  return result;
}
