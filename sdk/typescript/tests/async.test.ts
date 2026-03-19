/**
 * Async submit + query tests — submit batch_id, query later.
 */

import { describe, it, expect } from "vitest";
import {
  TEST_HTML_URL,
  TEST_MODEL,
  TEST_PDF_URL,
  getClient,
} from "./setup.js";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe("submit and getBatch", () => {
  it("submit returns batch id", async () => {
    const batchId = await getClient().submit(TEST_PDF_URL, {
      model: TEST_MODEL,
    });
    expect(typeof batchId).toBe("string");
    expect(batchId.length).toBeGreaterThan(0);
  });

  it("getBatch returns result", async () => {
    const batchId = await getClient().submit(TEST_PDF_URL, {
      model: TEST_MODEL,
    });
    const results = await getClient().getBatch(batchId);
    expect(results.length).toBeGreaterThanOrEqual(1);
    expect(["done", "pending", "running", "failed", "converting"]).toContain(
      results[0]!.state,
    );
  });

  it("getBatch eventually done", async () => {
    const batchId = await getClient().submit(TEST_HTML_URL, {
      model: "html",
    });

    let results = await getClient().getBatch(batchId);
    for (let i = 0; i < 120; i++) {
      if (results.every((r) => r.state === "done" || r.state === "failed")) break;
      await sleep(5000);
      results = await getClient().getBatch(batchId);
    }

    expect(results[0]!.state).toBe("done");
    expect(results[0]!.markdown).not.toBeNull();
  });
});

describe("submitBatch and getBatch", () => {
  it("submitBatch returns batch id", async () => {
    const batchId = await getClient().submitBatch(
      [TEST_PDF_URL, TEST_PDF_URL],
      { model: TEST_MODEL },
    );
    expect(typeof batchId).toBe("string");
    expect(batchId.length).toBeGreaterThan(0);
  });

  it("getBatch returns list", async () => {
    const batchId = await getClient().submitBatch([TEST_PDF_URL], {
      model: TEST_MODEL,
    });
    const results = await getClient().getBatch(batchId);
    expect(Array.isArray(results)).toBe(true);
    expect(results.length).toBeGreaterThanOrEqual(1);
  });
});
