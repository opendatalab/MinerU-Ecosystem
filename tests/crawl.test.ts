/**
 * Crawl tests — crawl a web page and parse to Markdown.
 */

import { describe, it, expect } from "vitest";
import { TEST_HTML_URL, TEST_TIMEOUT, getClient } from "./setup.js";

describe("crawl single page", () => {
  it("returns markdown", async () => {
    const result = await getClient().crawl(TEST_HTML_URL, {
      timeout: TEST_TIMEOUT,
    });

    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
    expect(result.markdown!.length).toBeGreaterThan(0);
  });

  it("equivalent to extract with html model", async () => {
    const result = await getClient().extract(TEST_HTML_URL, {
      model: "html",
      timeout: TEST_TIMEOUT,
    });

    expect(result.state).toBe("done");
    expect(result.markdown).not.toBeNull();
  });
});
