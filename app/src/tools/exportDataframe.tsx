import React, { useState } from 'react';
import communicationStore from "../store/communication"
import commonStore from '../store/common';

import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import LoadingIcon from '../components/loadingIcon';

import type { IAppProps } from '../interfaces';
import { parser_dsl_with_meta } from "@kanaries-temp/gw-dsl-parser";
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"
import type { VizSpecStore } from '@kanaries/graphic-walker/dist/store/visualSpecStore'

export function getExportDataframeTool(
    props: IAppProps,
    storeRef: React.MutableRefObject<VizSpecStore | null>
) : ToolbarButtonItem {
    const [exporting, setExporting] = useState(false);

    const exportSuccess = () => {
        commonStore.setNotification({
            type: "success",
            title: "Tips",
            message: <>
            <p className='py-1'>export success, created new dataframe: </p>
            <p className='font-semibold py-1'>`walker.last_exported_dataframe`</p>
            <p className='py-1'>if you forgot set variable walker, you can use</p>
            <p className='font-semibold py-1'>`pyg.GlobalVarManager.last_exported_dataframe`</p>
            <p className='py-1'>to get current exported dataframe</p>
            </>
        }, 20_000);

        setTimeout(() => {
            setExporting(false);
        }, 500);
    }

    const onClick = async () => {
        if (exporting) return;
        setExporting(true);
        try {
            if (props.parseDslType === "server") {
                await communicationStore.comm?.sendMsg("export_dataframe_by_payload", {
                    payload: {
                        workflow: storeRef.current?.workflow,
                    },
                    encodings: storeRef.current?.currentVis.encodings,
                });
            } else {
                const sql = parser_dsl_with_meta(
                    "pygwalker_mid_table",
                    JSON.stringify({workflow: storeRef.current?.workflow}),
                    JSON.stringify({"pygwalker_mid_table": props.fieldMetas})
                );
                await communicationStore.comm?.sendMsg("export_dataframe_by_sql", {
                    sql: sql,
                    encodings: storeRef.current?.currentVis.encodings,
                    timezoneOffsetSeconds: -new Date().getTimezoneOffset() * 60,
                });
            }
            exportSuccess();
        } catch (_) {
            setExporting(false);
        }
    }

    return {
        key: "export_dataframe",
        label: "export_dataframe",
        icon: (iconProps?: any) => {
            return exporting ? <LoadingIcon width={36} height={36} /> : <DocumentArrowDownIcon {...iconProps} />
        },
        onClick: onClick,
    }
}
