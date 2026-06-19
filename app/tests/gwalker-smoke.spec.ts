import { expect, test } from "@playwright/test";

const smokeProps = {
    id: "smoke",
    dataSource: [
        { city: "London", value: 1 },
        { city: "Tokyo", value: 2 },
    ],
    len: 2,
    version: "0.5.0.1",
    hashcode: "smoke-user",
    userConfig: { privacy: "offline" },
    visSpec: [
        {
            visId: "smoke-chart",
            name: "Smoke chart",
            config: {
                defaultAggregated: true,
                geoms: ["bar"],
                coordSystem: "generic",
                limit: -1,
            },
            encodings: {
                dimensions: [
                    {
                        dragId: "gw-city",
                        fid: "city",
                        name: "city",
                        basename: "city",
                        semanticType: "nominal",
                        analyticType: "dimension",
                        offset: 0,
                    },
                ],
                measures: [
                    {
                        dragId: "gw-value",
                        fid: "value",
                        name: "value",
                        basename: "value",
                        semanticType: "quantitative",
                        analyticType: "measure",
                        aggName: "sum",
                        offset: 0,
                    },
                ],
                rows: [
                    {
                        dragId: "gw-row-value",
                        fid: "value",
                        name: "value",
                        basename: "value",
                        semanticType: "quantitative",
                        analyticType: "measure",
                        aggName: "sum",
                        offset: 0,
                    },
                ],
                columns: [
                    {
                        dragId: "gw-column-city",
                        fid: "city",
                        name: "city",
                        basename: "city",
                        semanticType: "nominal",
                        analyticType: "dimension",
                        offset: 0,
                    },
                ],
                color: [],
                opacity: [],
                size: [],
                shape: [],
                theta: [],
                radius: [],
                longitude: [],
                latitude: [],
                geoId: [],
                details: [],
                filters: [],
                text: [],
            },
            layout: {
                showActions: false,
                showTableSummary: false,
                stack: "stack",
                interactiveScale: false,
                zeroScale: true,
                size: {
                    mode: "fixed",
                    width: 480,
                    height: 320,
                },
                format: {},
                geoKey: "name",
                resolve: {
                    x: false,
                    y: false,
                    color: false,
                    opacity: false,
                    shape: false,
                    size: false,
                },
                scaleIncludeUnmatchedChoropleth: false,
                useSvg: false,
            },
        },
    ],
    rawFields: [
        {
            fid: "city",
            name: "city",
            semanticType: "nominal",
            analyticType: "dimension",
            offset: 0,
        },
        {
            fid: "value",
            name: "value",
            semanticType: "quantitative",
            analyticType: "measure",
            offset: 0,
        },
    ],
    fieldkeyGuard: false,
    themeKey: "g2",
    dark: "light",
    sourceInvokeCode: "",
    dataSourceProps: {
        tunnelId: "tunnel!",
        dataSourceId: "smoke-data",
    },
    env: "anywidget",
    specType: "empty_string",
    needLoadDatas: false,
    showCloudTool: false,
    enableAskViz: false,
    enableVlChat: false,
    needInitChart: false,
    useKernelCalc: false,
    useSaveTool: false,
    parseDslType: "client",
    communicationUrl: "",
    gwMode: "explore",
    needLoadLastSpec: false,
    datasetType: "pandas_dataframe",
    extraConfig: {},
    fieldMetas: [
        { key: "city", type: "string" },
        { key: "value", type: "number" },
    ],
    isExportDataFrame: false,
    defaultTab: "vis",
    useCloudCalc: false,
};

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
