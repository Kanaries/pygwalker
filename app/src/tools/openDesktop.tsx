import React from "react";

import { tracker } from "@/utils/tracker";
import { ComputerDesktopIcon } from "@heroicons/react/24/outline";

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";
import { IAppProps } from "@/interfaces";
import { VizSpecStore } from "@kanaries/graphic-walker";
import communicationStore from "@/store/communication";

export function getOpenDesktopTool(props: IAppProps, storeRef: React.MutableRefObject<VizSpecStore | null>): ToolbarButtonItem {
    const onClick = async () => {
        tracker.track("click", { entity: "open_desktop_icon" });
        await communicationStore.comm?.sendMsg("open_in_desktop", {
            spec: JSON.parse(JSON.stringify(storeRef.current?.visList)),
            fields: JSON.parse(JSON.stringify(storeRef.current?.meta)),
        });
    };
    return {
        key: "open_in_desktop",
        label: "open_desktop",
        icon: (iconProps?: any) => <ComputerDesktopIcon {...iconProps} />,
        onClick,
    };
}
