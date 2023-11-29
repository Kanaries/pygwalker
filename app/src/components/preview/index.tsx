import React from "react";
import { observer } from "mobx-react-lite";
import pako from "pako";
import { PureRenderer } from '@kanaries/graphic-walker';
import type { IThemeKey } from '@kanaries/graphic-walker/dist/interfaces';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
// @ts-ignore
import style from '@/index.css?inline'

interface IPreviewProps {
    themeKey: string;
    charts: {
        visSpec: any;
        data: string;
    }[];
}

const getInflateData = (dataStr: string) => {
    let binaryString = atob(dataStr);
    let compressed = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        compressed[i] = binaryString.charCodeAt(i);
    }
    const inflated = pako.inflate(compressed, {to: "string"});
    const datas = JSON.parse(inflated);
    const keys = Object.keys(datas);
    if (keys.length === 0) {
        return [];
    }
    const count = datas[keys[0]].length;

    const result = [] as any[];
    for (let i = 0; i < count; i++) {
        let item = {};
        keys.forEach(key => {
            item[key] = datas[key][i]
        })
        result.push(item);
    }

    return result;
}

const Preview: React.FC<IPreviewProps> = observer((props) => {
    const { charts, themeKey } = props;
    const formatedCharts = charts.map((chart) => {
        return {
            ...chart,
            data: getInflateData(chart.data)
        }
    })

    return (
        <React.StrictMode>
            <style>{style}</style>
            <Tabs defaultValue="0" className="w-full">
                <div className="overflow-x-auto max-w-full">
                    <TabsList>
                        {formatedCharts.map((chart, index) => {
                            return <TabsTrigger key={index} value={index.toString()}>{chart.visSpec.name}</TabsTrigger>
                        })}
                    </TabsList>
                </div>
                {formatedCharts.map((chart, index) => {
                    return <TabsContent key={index} value={index.toString()}>
                        <PureRenderer
                            themeKey={themeKey as IThemeKey}
                            name={chart.visSpec.name}
                            visualConfig={chart.visSpec.config}
                            visualLayout={chart.visSpec.layout}
                            visualState={chart.visSpec.encodings}
                            type='remote'
                            computation={async(_) => { return chart.data }}
                        />
                    </TabsContent>
                })}
            </Tabs>
        </React.StrictMode>
    );
});

interface IChartPreviewProps {
    themeKey: string;
    visSpec: any;
    data: string;
    title: string;
    desc: string;
}

const ChartPreview: React.FC<IChartPreviewProps> = observer((props) => {
    const formatedData = getInflateData(props.data);

    return (
        <React.StrictMode>
            <div>
                <h1 style={{marginTop: "1rem", color: "#333", fontSize: "1.1rem", marginBottom: "0.5rem", paddingInlineStart: "1rem"}}>{ props.title }</h1>
                <p style={{color: "#666", fontWeight: 300, paddingInlineStart: "1rem"}}>{ props.desc }</p>
                <PureRenderer
                    themeKey={props.themeKey as IThemeKey}
                    name={props.visSpec.name}
                    visualConfig={props.visSpec.config}
                    visualLayout={props.visSpec.layout}
                    visualState={props.visSpec.encodings}
                    type='remote'
                    computation={async(_) => { return formatedData }}
                />
            </div>
        </React.StrictMode>
    );
});


export {
    Preview,
    ChartPreview,
};

export type {
    IPreviewProps,
    IChartPreviewProps
}
