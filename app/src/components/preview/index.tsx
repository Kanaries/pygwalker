import React from "react";
import { observer } from "mobx-react-lite";
import { PureRenderer, IRow } from '@kanaries/graphic-walker';
import type { IDarkMode, IThemeKey } from '@kanaries/graphic-walker/interfaces';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
// @ts-ignore
import style from '@/index.css?inline'

interface IPreviewProps {
    themeKey: string;
    dark: IDarkMode;
    charts: {
        visSpec: any;
        data: IRow[];
    }[];
}

const Preview: React.FC<IPreviewProps> = observer((props) => {
    const { charts, themeKey } = props;

    return (
        <React.StrictMode>
            <div className="bg-background text-foreground">
                <style>{style}</style>
                <Tabs defaultValue="0" className="w-full">
                    <div className="overflow-x-auto max-w-full">
                        <TabsList>
                            {charts.map((chart, index) => {
                                return <TabsTrigger key={index} value={index.toString()}>{chart.visSpec.name}</TabsTrigger>
                            })}
                        </TabsList>
                    </div>
                    {charts.map((chart, index) => {
                        return <TabsContent key={index} value={index.toString()}>
                            <PureRenderer
                                vizThemeConfig={themeKey as IThemeKey}
                                name={chart.visSpec.name}
                                visualConfig={chart.visSpec.config}
                                visualLayout={chart.visSpec.layout}
                                visualState={chart.visSpec.encodings}
                                type='remote'
                                computation={async(_) => { return chart.data }}
                                appearance={props.dark as IDarkMode}
                            />
                        </TabsContent>
                    })}
                </Tabs>
            </div>
        </React.StrictMode>
    );
});

interface IChartPreviewProps {
    themeKey: string;
    dark: IDarkMode;
    visSpec: any;
    data: IRow[];
    title: string;
    desc: string;
}

const ChartPreview: React.FC<IChartPreviewProps> = observer((props) => {

    return (
        <React.StrictMode>
            <div>
                <h1 style={{marginTop: "1rem", color: "#333", fontSize: "1.1rem", marginBottom: "0.5rem", paddingInlineStart: "1rem"}}>{ props.title }</h1>
                <p style={{color: "#666", fontWeight: 300, paddingInlineStart: "1rem"}}>{ props.desc }</p>
                <PureRenderer
                    vizThemeConfig={props.themeKey as IThemeKey}
                    name={props.visSpec.name}
                    visualConfig={props.visSpec.config}
                    visualLayout={props.visSpec.layout}
                    visualState={props.visSpec.encodings}
                    type='remote'
                    computation={async(_) => { return props.data }}
                    appearance={props.dark as IDarkMode}
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
