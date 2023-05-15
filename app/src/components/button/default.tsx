import React from "react";
import { ButtonBaseProps } from "./base";

const DefaultButton: React.FC<ButtonBaseProps> = (props) => {
    const { text, onClick, disabled, className } = props;
    let btnClassName = "inline-flex items-center rounded border border-gray-300 bg-white dark:bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
    if (className) {
        btnClassName = btnClassName + " " + className;
    }
    return (
        <button
            className={btnClassName}
            onClick={onClick}
            disabled={disabled}
        >
            {text}
        </button>
    );
};

export default DefaultButton;
