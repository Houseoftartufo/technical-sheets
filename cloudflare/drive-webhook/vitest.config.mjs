import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          DRIVE_WEBHOOK_TOKEN: "fixture-drive-token",
          DRIVE_STATE_API_TOKEN: "fixture-state-token",
          GITHUB_DISPATCH_TOKEN: "fixture-github-token",
        },
      },
    }),
  ],
  test: {
    include: ["test/**/*.test.mjs"],
    testTimeout: 15_000,
  },
});
