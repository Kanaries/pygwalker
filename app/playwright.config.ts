import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
    testDir: "./tests",
    timeout: 30_000,
    expect: {
        timeout: 10_000,
    },
    use: {
        ...devices["Desktop Chrome"],
        baseURL: "http://127.0.0.1:8769",
        trace: "on-first-retry",
    },
    webServer: {
        command: "yarn dev --host 127.0.0.1",
        url: "http://127.0.0.1:8769",
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
    },
});
