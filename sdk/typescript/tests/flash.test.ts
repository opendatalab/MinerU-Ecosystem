/**
 * Flash mode tests — unit tests (no API) + integration tests (real API).
 */

import { describe, it, expect } from "vitest";
import { writeFile, mkdtemp, stat } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  MinerU,
  NoAuthClientError,
  saveMarkdown,
  saveDocx,
  saveHtml,
  saveLatex,
} from "../src/index.js";

const FLASH_TEST_PDF_URL =
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf";
const FLASH_TEST_TIMEOUT = 300;

// ═══════════════════════════════════════════════════════════════════
//  Unit tests — no API calls
// ═══════════════════════════════════════════════════════════════════

describe("flash-only client (unit)", () => {
  const origToken = process.env["MINERU_TOKEN"];

  async function withoutToken(fn: () => Promise<void> | void): Promise<void> {
    delete process.env["MINERU_TOKEN"];
    try {
      await fn();
    } finally {
      if (origToken != null) {
        process.env["MINERU_TOKEN"] = origToken;
      }
    }
  }

  it("creates client without token", () => {
    withoutToken(() => {
      const c = new MinerU();
      expect(c).toBeDefined();
    });
  });

  it("extract throws NoAuthClientError", async () => {
    await withoutToken(async () => {
      const c = new MinerU();
      await expect(c.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")).rejects.toThrow(
        NoAuthClientError,
      );
    });
  });

  it("crawl throws NoAuthClientError", async () => {
    await withoutToken(async () => {
      const c = new MinerU();
      await expect(c.crawl("https://example.com")).rejects.toThrow(
        NoAuthClientError,
      );
    });
  });

  it("submit throws NoAuthClientError", async () => {
    await withoutToken(async () => {
      const c = new MinerU();
      await expect(c.submit("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")).rejects.toThrow(
        NoAuthClientError,
      );
    });
  });

  it("getTask throws NoAuthClientError", async () => {
    await withoutToken(async () => {
      const c = new MinerU();
      await expect(c.getTask("fake-id")).rejects.toThrow(NoAuthClientError);
    });
  });
});

// ═══════════════════════════════════════════════════════════════════
//  Integration tests — flash API (no token needed)
// ═══════════════════════════════════════════════════════════════════

describe("flash extract URL", () => {
  const client = new MinerU();

  it("returns done with markdown", async () => {
    const result = await client.flashExtract(FLASH_TEST_PDF_URL, {
      pageRange: "1-3",
      timeout: FLASH_TEST_TIMEOUT,
    });

    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
    expect(result.markdown!.length).toBeGreaterThan(0);
    expect(result.taskId).toBeTruthy();
  });

  it("with language option", async () => {
    const result = await client.flashExtract(FLASH_TEST_PDF_URL, {
      language: "en",
      pageRange: "1-1",
      timeout: FLASH_TEST_TIMEOUT,
    });

    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
  });
});

describe("flash extract local file", () => {
  const client = new MinerU();

  it("local PDF returns markdown", async () => {
    const pdfBytes = Buffer.from(
      "%PDF-1.0\n" +
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" +
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n" +
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n" +
        "4 0 obj\n<< /Length 44 >>\nstream\n" +
        "BT /F1 24 Tf 100 700 Td (Hello MinerU) Tj ET\n" +
        "endstream\nendobj\n" +
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n" +
        "xref\n0 6\n" +
        "0000000000 65535 f \n" +
        "0000000009 00000 n \n" +
        "0000000058 00000 n \n" +
        "0000000115 00000 n \n" +
        "0000000266 00000 n \n" +
        "0000000360 00000 n \n" +
        "trailer\n<< /Size 6 /Root 1 0 R >>\n" +
        "startxref\n435\n%%EOF\n",
    );

    const dir = await mkdtemp(join(tmpdir(), "mineru-test-"));
    const path = join(dir, "test_hello.pdf");
    await writeFile(path, pdfBytes);

    const result = await client.flashExtract(path, {
      timeout: FLASH_TEST_TIMEOUT,
    });
    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
  });
});

describe("flash extract save", () => {
  const client = new MinerU();

  it("save markdown works", async () => {
    const result = await client.flashExtract(FLASH_TEST_PDF_URL, {
      pageRange: "1-1",
      timeout: FLASH_TEST_TIMEOUT,
    });

    const dir = await mkdtemp(join(tmpdir(), "mineru-test-"));
    const out = join(dir, "output.md");
    await saveMarkdown(result, out, false);
    const s = await stat(out);
    expect(s.size).toBeGreaterThan(0);
  });

  it("save docx/html/latex raises", async () => {
    const result = await client.flashExtract(FLASH_TEST_PDF_URL, {
      pageRange: "1-1",
      timeout: FLASH_TEST_TIMEOUT,
    });

    await expect(
      saveDocx(result, join(tmpdir(), "out.docx")),
    ).rejects.toThrow();
    await expect(
      saveHtml(result, join(tmpdir(), "out.html")),
    ).rejects.toThrow();
    await expect(
      saveLatex(result, join(tmpdir(), "out.tex")),
    ).rejects.toThrow();
  });
});
