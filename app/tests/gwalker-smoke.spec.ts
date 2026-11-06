import { expect, test } from "@playwright/test";
import { resolve } from "node:path";

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

for (const gwMode of ["renderer", "filter_renderer", "table"]) {
    test(`renders local data in ${gwMode} mode`, async ({ page }) => {
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(error.message));
        await page.goto("/");
        await page.evaluate(props => {
            window.postMessage({ type: "pyg_props", data: props }, "*");
        }, {
            ...smokeProps,
            gwMode,
            // SVG exposes the plotted labels so these checks verify the data reached the chart.
            visSpec: smokeProps.visSpec.map(spec => ({
                ...spec,
                layout: { ...spec.layout, useSvg: true },
            })),
        });

        await expect(page.getByText("London", { exact: true }).first()).toBeVisible();
        await expect(page.getByText("Tokyo", { exact: true }).first()).toBeVisible();
        if (gwMode === "table") {
            await expect(page.getByText("city", { exact: true }).first()).toBeVisible();
            await expect(page.getByText("value", { exact: true }).first()).toBeVisible();
        } else {
            await expect(page.locator("svg.marks")).toBeVisible();
        }
        expect(errors).toEqual([]);
    });
}

test("keeps the production entrypoints and renders an anywidget model", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    // Run yarn build first, as CI does, so this bundle reflects the current source.
    // The Python anywidget path loads this standalone production ESM bundle.
    await page.route("**/__test__/pygwalker-app.es.js", route => route.fulfill({
        path: resolve(__dirname, "../../pygwalker/templates/dist/pygwalker-app.es.js"),
        contentType: "text/javascript",
    }));
    await page.goto("/");
    const exports = await page.evaluate(async props => {
        const { default: app } = await import("/__test__/pygwalker-app.es.js");
        const el = document.createElement("div");
        el.id = "anywidget-test";
        document.body.append(el);
        const listeners = new Map<string, Set<(message: any) => void>>();
        const requests: any[] = [];
        const model = {
            get: (name: string) => name === "props"
                ? JSON.stringify({ ...props, needLoadLastSpec: true })
                : undefined,
            on: (event: string, callback: (message: any) => void) => {
                if (!listeners.has(event)) listeners.set(event, new Set());
                listeners.get(event)!.add(callback);
            },
            off: (event: string, callback: (message: any) => void) => listeners.get(event)?.delete(callback),
            send: (message: any) => {
                requests.push(message);
                const { gid, rid, action } = message.msg;
                if (action !== "get_latest_vis_spec") throw new Error(`Unexpected request: ${action}`);
                queueMicrotask(() => {
                    const response = {
                        type: "pyg_response",
                        data: JSON.stringify({
                            gid,
                            rid,
                            action: "finish_request",
                            data: {
                                code: 0,
                                data: { visSpec: props.visSpec.map(spec => ({ ...spec, name: "Restored chart" })) },
                                message: "success",
                            },
                        }),
                    };
                    listeners.get("msg:custom")?.forEach(callback => callback(response));
                });
            },
        };
        (window as any).anywidgetRequests = requests;
        (window as any).disposeAnywidget = await app.render({ el, model, experimental: {} });
        return Object.fromEntries(Object.entries(app).map(([key, value]) => [key, typeof value]));
    }, smokeProps);

    expect(exports).toEqual({
        GWalker: "function",
        PreviewApp: "function",
        ChartPreviewApp: "function",
        StreamlitGWalker: "function",
        mountPygWalker: "function",
        render: "function",
    });
    const widget = page.locator("#anywidget-test");
    await expect(widget.getByText("Restored chart").first()).toBeVisible();
    await expect(widget.getByText("value", { exact: true }).first()).toBeVisible();
    await expect(widget.locator("canvas").last()).toBeVisible();
    expect(await page.evaluate(() => (window as any).anywidgetRequests.length)).toBeGreaterThan(0);
    await page.evaluate(() => (window as any).disposeAnywidget());
    await expect(widget).toHaveJSProperty("childElementCount", 0);
    expect(errors).toEqual([]);
});
