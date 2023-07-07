import React from 'react';

import { UserIcon } from '@heroicons/react/24/outline';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"


export function getLoginTool(
    setMounted: React.Dispatch<React.SetStateAction<boolean>>,
    wrapRef: React.MutableRefObject<HTMLElement | null>,
) : ToolbarButtonItem {
    return {
        key: 'login',
        label: 'login',
        icon: (iconProps?: any) => (
            <UserIcon {...iconProps} ref={e => {
            setMounted(true);
            wrapRef.current = e?.parentElement as HTMLElement;
            }} />
        ),
        onClick: () => {}
    }
}
