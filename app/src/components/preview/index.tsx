import React from "react";
import { observer } from "mobx-react-lite";
import pako from "pako";
import { PureRenderer } from '@kanaries/graphic-walker';
import type { IThemeKey } from '@kanaries/graphic-walker/dist/interfaces';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
// @ts-ignore
import style from '@/index.css?inline'
import { PreviewAppProps } from "@/interfaces";

interface IPreview extends PreviewAppProps {
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

const Preview: React.FC<IPreview> = observer((props) => {
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

export default Preview;
