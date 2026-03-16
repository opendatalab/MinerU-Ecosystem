/**
 * Shared constants and client setup for integration tests.
 *
 * These tests hit the real MinerU API. Requires MINERU_TOKEN env var.
 */

import { MinerU, type ExtractResult } from "../src/index.js";

export const TEST_PDF_URL = "https://bitcoin.org/bitcoin.pdf";
export const TEST_MODEL = "pipeline";
export const TEST_HTML_URL = "https://www.example.com";
export const TEST_TIMEOUT = 600;

let _client: MinerU | null = null;
let _pdfResult: ExtractResult | null = null;
let _localPdfResult: ExtractResult | null = null;

export function getClient(): MinerU {
  if (!_client) {
    _client = new MinerU();
  }
  return _client;
}

export async function getPdfResult(): Promise<ExtractResult> {
  if (!_pdfResult) {
    _pdfResult = await getClient().extract(TEST_PDF_URL, {
      model: TEST_MODEL,
      extraFormats: ["docx"],
      timeout: TEST_TIMEOUT,
    });
  }
  return _pdfResult;
}

export async function getLocalPdfResult(): Promise<ExtractResult> {
  if (!_localPdfResult) {
    const { writeFile, mkdtemp } = await import("node:fs/promises");
    const { join } = await import("node:path");
    const { tmpdir } = await import("node:os");

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

    _localPdfResult = await getClient().extract(path, {
      model: TEST_MODEL,
      timeout: TEST_TIMEOUT,
    });
  }
  return _localPdfResult;
}
