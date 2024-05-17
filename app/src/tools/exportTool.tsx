import React from 'react';

import { tracker } from "@/utils/tracker";
import { CodeBracketSquareIcon } from '@heroicons/react/24/outline';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"


export function getExportTool(
    setExportOpen: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    const onClick = () => {
        setExportOpen(true);
        tracker.track("click", {"entity": "export_code_icon"});
    }
    return {
        key: "export_pygwalker_code",
        label: "export_code",
        icon: (iconProps?: any) => <CodeBracketSquareIcon {...iconProps} />,
        onClick
    }
}
