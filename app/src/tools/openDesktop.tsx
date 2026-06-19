import React from "react";

import { tracker } from "@/utils/tracker";
import { ComputerDesktopIcon } from "@heroicons/react/24/outline";

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";
import type { IAppProps, ICommEmptyResponse, ICommOpenDesktopRequest } from "@/interfaces";
import { VizSpecStore } from "@kanaries/graphic-walker";
import communicationStore from "@/store/communication";

export function getOpenDesktopTool(props: IAppProps, storeRef: React.MutableRefObject<VizSpecStore | null>): ToolbarButtonItem {
    const onClick = async () => {
        tracker.track("click", { entity: "open_desktop_icon" });
        const request: ICommOpenDesktopRequest = {
            spec: JSON.parse(JSON.stringify(storeRef.current?.visList)),
            fields: JSON.parse(JSON.stringify(storeRef.current?.meta)),
        };
        await communicationStore.comm?.sendMsg<ICommEmptyResponse>("open_in_desktop", request);
    };
    return {
        key: "open_in_desktop",
        label: "open_desktop",
        icon: (iconProps?: any) => <ComputerDesktopIcon {...iconProps} />,
        onClick,
    };
}
