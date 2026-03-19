import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    testTimeout: 700_000,
    hookTimeout: 700_000,
  },
});
