/**
 * Async submit + query tests — submit task_id / batch_id, query later.
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

describe("submit and getTask", () => {
  it("submit returns task id", async () => {
    const taskId = await getClient().submit(TEST_PDF_URL, {
      model: TEST_MODEL,
    });
    expect(typeof taskId).toBe("string");
    expect(taskId.length).toBeGreaterThan(0);
  });

  it("getTask returns result", async () => {
    const taskId = await getClient().submit(TEST_PDF_URL, {
      model: TEST_MODEL,
    });
    const result = await getClient().getTask(taskId);
    expect(["done", "pending", "running", "failed", "converting"]).toContain(
      result.state,
    );
  });

  it("getTask eventually done", async () => {
    const taskId = await getClient().submit(TEST_HTML_URL, {
      model: "html",
    });

    let result = await getClient().getTask(taskId);
    for (let i = 0; i < 120; i++) {
      if (result.state === "done" || result.state === "failed") break;
      await sleep(5000);
      result = await getClient().getTask(taskId);
    }

    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
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
