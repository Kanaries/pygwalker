import React from "react";

import { tracker } from "@/utils/tracker";
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";

const RUNCELL_LOGO_URL = "https://www.runcell.dev/runcell-logo.svg";
const RUNCELL_WEBSITE = "https://www.runcell.dev?utm_source=pygwalker";

export function getRuncellTool(): ToolbarButtonItem {
    const onClick = () => {
        tracker.track("click", { entity: "runcell_icon" });
        window.open(RUNCELL_WEBSITE, "_blank");
    };

    return {
        key: "runcell",
        label: "AI Agent",
        icon: (iconProps?: any) => (
            <img
                src={RUNCELL_LOGO_URL}
                alt="Jupyter AI Agent"
                style={{
                    width: iconProps?.width || 20,
                    height: iconProps?.height || 20,
                }}
            />
        ),
        onClick,
    };
}
