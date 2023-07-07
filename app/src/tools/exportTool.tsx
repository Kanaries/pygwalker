import React from 'react';

import { CodeBracketSquareIcon } from '@heroicons/react/24/outline';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"


export function getExportTool(
    setExportOpen: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    return {
        key: "export_code",
        label: "export_code",
        icon: (iconProps?: any) => <CodeBracketSquareIcon {...iconProps} />,
        onClick: () => { setExportOpen(true); }
    }
}
