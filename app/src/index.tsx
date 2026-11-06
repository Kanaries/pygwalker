import { createRender } from '@anywidget/react';
import { GWalker, PreviewApp, ChartPreviewApp, StreamlitGWalker, mountPygWalker, AnywidgetGWalkerApp } from './app/hosts';

export type { IPygWalkerTheme } from './app/shell';
export type { IPygWalkerMount } from './app/hosts';

export default {
    GWalker,
    PreviewApp,
    ChartPreviewApp,
    StreamlitGWalker,
    mountPygWalker,
    render: createRender(AnywidgetGWalkerApp),
}
