/**
 * Extract tests — single PDF, local file, extra formats.
 */

import { describe, it, expect } from "vitest";
import { stat, mkdtemp } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { saveDocx } from "../src/index.js";
import { getPdfResult, getLocalPdfResult } from "./setup.js";

describe("extract single PDF", () => {
  it("returns done with markdown", async () => {
    const result = await getPdfResult();
    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
    expect(result.markdown!.length).toBeGreaterThan(0);
  });

  it("has content list", async () => {
    const result = await getPdfResult();
    expect(result.contentList).not.toBeNull();
    expect(Array.isArray(result.contentList)).toBe(true);
  });

  it("has metadata", async () => {
    const result = await getPdfResult();
    expect(result.taskId).toBeTruthy();
    expect(result.zipUrl).not.toBeNull();
    expect(result.error).toBeNull();
  });
});

describe("extract local file", () => {
  it("local PDF returns markdown", async () => {
    const result = await getLocalPdfResult();
    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
  });
});

describe("extract with extra formats", () => {
  it("docx export", async () => {
    const result = await getPdfResult();
    expect(result.state).toBe("done");
    expect(result.docx).not.toBeNull();
    expect(result.docx!.length).toBeGreaterThan(0);
  });

  it("save docx to file", async () => {
    const result = await getPdfResult();
    const dir = await mkdtemp(join(tmpdir(), "mineru-test-"));
    const out = join(dir, "report.docx");
    await saveDocx(result, out);
    const s = await stat(out);
    expect(s.size).toBeGreaterThan(0);
  });
});
