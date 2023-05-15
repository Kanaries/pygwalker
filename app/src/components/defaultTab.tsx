import React, { ReactElement } from "react";

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
}

export interface ITabOption {
    label: string | ReactElement;
    key: string;
    disabled?: boolean;
}
interface DefaultProps {
    tabs: ITabOption[];
    selectedKey: string;
    onSelected: (selectedKey: string, index: number) => void;
    allowEdit?: boolean;
    onEditLabel?: (label: string, index: number) => void;
}
export default function Default(props: DefaultProps) {
    const { tabs, selectedKey, onSelected } = props;

    return (
        <div className="border-b border-gray-200 dark:border-gray-700 mb-2" >
            <nav className="-mb-px flex space-x-8" role="tablist" aria-label="Tabs">
                {tabs.map((tab, tabIndex) => (
                    <span
                        role="tab"
                        tabIndex={0}
                        onClick={() => {
                            !tab.disabled && onSelected(tab.key, tabIndex)
                        }}
                        key={tab.key}
                        className={classNames(
                            tab.key === selectedKey
                            ? 'border-indigo-500 text-indigo-600 dark:border-indigo-400 dark:text-indigo-300'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-300 dark:text-gray-400',
                          'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm cursor-pointer',
                            tab.disabled ? 'opacity-50 cursor-not-allowed' : ''
                        )}
                    >{tab.label}</span>
                ))}
            </nav>
        </div>
    );
}
