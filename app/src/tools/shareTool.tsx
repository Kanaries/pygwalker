import React from 'react';

import { ArrowUpCircleIcon } from '@heroicons/react/24/outline';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"

export function getShareTool(
    setShareModalOpen: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    return {
        key: "upload_charts",
        label: "upload_charts",
        icon: (iconProps?: any) => {
            return <ArrowUpCircleIcon {...iconProps} />
        },
        onClick: () => { setShareModalOpen(true); },
    }
}
