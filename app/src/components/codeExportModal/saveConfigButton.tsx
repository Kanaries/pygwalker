
import React, { Fragment, useState, useEffect, useMemo } from "react";
import { download } from "../../utils/save";
import { Menu, Transition } from "@headlessui/react";
import commonStore from "../../store/common";

import type { IVisSpec } from '@kanaries/graphic-walker/dist/interfaces'


interface IDsaveConfigButtonProps {
    sourceCode: string;
    configJson: IVisSpec[];
    setPygCode: (code: string) => void;
    setTips: (tips: string) => void;
}

const saveConfigButton: React.FC<IDsaveConfigButtonProps> = (props) => {
    const sourceCode = props.sourceCode;
    const [saving, setSaving] = useState<boolean>(false);
    const pygConfig = useMemo(() => {
        return JSON.stringify({
            "config": JSON.stringify(props.configJson),
            "chart_map": {},
            "version": commonStore.version,
        })
    }, [props.configJson])

    const saveAsCode = () => {
        const preCode = sourceCode.replace("'____pyg_walker_spec_params____'", "vis_spec")
        const code = `vis_spec = r"""${pygConfig}"""\n${preCode}`;
        props.setPygCode(code);
    }

    const saveAsFile = () => {
        setSaving(true);
        const code = sourceCode.replace("____pyg_walker_spec_params____", "local file path")
        download(pygConfig, "config.json", "text/plain");
        props.setPygCode(code);
        setSaving(false);
    }

    useEffect(() => {
        saveAsCode()
    }, [props.configJson])

    return (
        <Menu as="span" className="relative block text-left">
            <Menu.Button
                className="mr-2 px-6 inline-flex items-center rounded border border-gray-300 bg-white dark:bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                disabled={saving}
            >
                { saving ? "Exporting" : "Export As" }
            </Menu.Button>

            <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
            >
                <Menu.Items className="-top-2 transform -translate-y-full absolute absolute left-0 mt-2 w-34 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div className="px-1 py-1">
                        <Menu.Item>
                            <button
                                className="group flex w-full items-center rounded-md px-2 py-2 text-sm"
                                onClick={saveAsCode}
                            >
                                Code
                            </button>
                        </Menu.Item>
                        <Menu.Item>
                            <button
                                className="group flex w-full items-center rounded-md px-2 py-2 text-sm"
                                onClick={saveAsFile}
                            >
                                File
                            </button>
                        </Menu.Item>
                    </div>
                </Menu.Items>
            </Transition>
        </Menu>
    );
};

export default saveConfigButton;
