/**
 * Batch tests — extractBatch and crawlBatch.
 */

import { describe, it, expect } from "vitest";
import { TEST_MODEL, TEST_PDF_URL, TEST_TIMEOUT, getClient } from "./setup.js";

describe("extractBatch", () => {
  it("yields all results", async () => {
    const urls = [TEST_PDF_URL, TEST_PDF_URL];
    const results = [];
    for await (const r of getClient().extractBatch(urls, {
      model: TEST_MODEL,
      timeout: TEST_TIMEOUT,
    })) {
      results.push(r);
    }

    expect(results.length).toBe(2);
    for (const r of results) {
      expect(["done", "failed"]).toContain(r.state);
    }
  });

  it("done results have markdown", async () => {
    const urls = [TEST_PDF_URL, TEST_PDF_URL];
    for await (const result of getClient().extractBatch(urls, {
      model: TEST_MODEL,
      timeout: TEST_TIMEOUT,
    })) {
      if (result.state === "done") {
        expect(result.markdown).not.toBeNull();
        expect(result.markdown!.length).toBeGreaterThan(0);
      }
    }
  });
});

describe("crawlBatch", () => {
  it("yields results", async () => {
    const urls = ["https://www.example.com", "https://www.example.org"];
    const results = [];
    for await (const r of getClient().crawlBatch(urls, {
      timeout: TEST_TIMEOUT,
    })) {
      results.push(r);
    }

    expect(results.length).toBe(2);
    for (const r of results) {
      expect(["done", "failed"]).toContain(r.state);
    }
  });
});
