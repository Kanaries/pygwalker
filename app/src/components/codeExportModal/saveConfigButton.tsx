
import React, { Fragment, useState, useEffect } from "react";
import { download } from "../../utils/save";
import { Menu, Transition } from "@headlessui/react";
import { getToken } from "@kanaries/auth-wrapper";
import { checkUploadPrivacy } from "../../utils/userConfig";
import { encodeSpec } from "../../utils/graphicWalkerParser"
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

    const saveAsCode = () => {
        const preCode = sourceCode.replace("'____pyg_walker_spec_params____'", "vis_spec")
        const code = `vis_spec = """${encodeSpec(props.configJson)}"""\n${preCode}`;
        props.setPygCode(code);
    }

    const saveAsFile = () => {
        setSaving(true);
        const code = sourceCode.replace("____pyg_walker_spec_params____", "local file path")
        download(encodeSpec(props.configJson), "config.json", "text/plain");
        props.setPygCode(code);
        setSaving(false);
    }

    const saveAsServer = async() => {
        setSaving(true);
        let token: string;
        try {
            token = await getToken();
        } catch (e) {
            props.setTips("get token timeout, please try again later or login again.")
            setSaving(false);
            return
        }
        try {
            const resp = await fetch(
                "https://i4rwxmw117.execute-api.us-east-1.amazonaws.com/default/pygwalker-config",
                {
                    method: "POST",
                    body: JSON.stringify({
                        token: token,
                        params: {
                            "config_json": encodeSpec(props.configJson),
                        }
                    })
                }
              )
              const respJson = await resp.json();
              if (respJson["code"] !== 0) {
                props.setTips("auth failed, if needed export as config id, please login again.")
                return
              }
              const configId = respJson["data"]["config_id"]
              const code = sourceCode.replace("____pyg_walker_spec_params____", configId)
              props.setPygCode(code);
              props.setTips("generate config id success!");
        } catch (e) {
            props.setTips("unknown error, please try again later.")
        } finally {
            setSaving(false);
        }
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
                        <Menu.Item>
                            <div className="group relative w-max">
                                <button
                                    className="group flex w-full items-center rounded-md px-2 py-2 text-sm disabled:opacity-50"
                                    onClick={saveAsServer}
                                    disabled={!checkUploadPrivacy() || !commonStore.showCloudTool}
                                >
                                    Config Id
                                </button>
                                {
                                    (!checkUploadPrivacy() || !commonStore.showCloudTool) &&
                                    <span
                                        className="absolute w-60 top-10 scale-0 rounded bg-gray-800 p-2 text-xs text-white group-hover:scale-100"
                                    >
                                        you need set your privacy to meta or any to use this feature and set `show_cloud_tool=True`.
                                    </span>
                                }
                            </div>
                        </Menu.Item>
                    </div>
                </Menu.Items>
            </Transition>
        </Menu>
    );
};

export default saveConfigButton;
