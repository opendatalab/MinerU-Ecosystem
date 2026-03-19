/**
 * CJS smoke test — verify the CommonJS require() path works.
 *
 * This test imports from the built dist/ output to ensure the CJS
 * bundle is valid. Run `npm run build` before running this test.
 */

import { describe, it, expect } from "vitest";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);

describe("CJS require smoke test", () => {
  it("require('mineru') exports MinerU class", () => {
    const distPath = resolve(import.meta.dirname, "../dist/index.cjs");
    const mod = require(distPath);

    expect(mod.MinerU).toBeDefined();
    expect(typeof mod.MinerU).toBe("function");
  });

  it("require('mineru') exports error classes", () => {
    const distPath = resolve(import.meta.dirname, "../dist/index.cjs");
    const mod = require(distPath);

    expect(mod.MinerUError).toBeDefined();
    expect(mod.AuthError).toBeDefined();
    expect(mod.TimeoutError).toBeDefined();
  });

  it("require('mineru') exports save helpers", () => {
    const distPath = resolve(import.meta.dirname, "../dist/index.cjs");
    const mod = require(distPath);

    expect(typeof mod.saveMarkdown).toBe("function");
    expect(typeof mod.saveDocx).toBe("function");
    expect(typeof mod.saveHtml).toBe("function");
    expect(typeof mod.saveLatex).toBe("function");
    expect(typeof mod.saveAll).toBe("function");
  });
});
