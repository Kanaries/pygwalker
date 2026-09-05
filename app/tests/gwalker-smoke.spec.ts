import { expect, test } from "@playwright/test";

import { smokeProps } from "./fixtures/props";

test("loads the Graphic Walker app and clicks a chart", async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on("console", (message) => {
        if (message.type() === "error") {
            consoleErrors.push(message.text());
        }
    });
    page.on("pageerror", (error) => {
        consoleErrors.push(error.message);
    });

    await page.goto("/");
    await page.evaluate((props) => {
        window.postMessage({ type: "pyg_props", data: props }, "*");
    }, smokeProps);

    await expect(page.getByText("Smoke chart").first()).toBeVisible();
    await expect(page.getByText("value", { exact: true }).first()).toBeVisible();

    const chart = page.locator("canvas, svg").first();
    await expect(chart).toBeVisible();
    await chart.click({ position: { x: 20, y: 20 } });

    expect(consoleErrors).toEqual([]);
});
