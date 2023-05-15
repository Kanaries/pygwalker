import React from "react";
import { ButtonBaseProps } from "./base";

const PrimaryButton: React.FC<ButtonBaseProps> = (props) => {
    const { text, onClick, disabled, className } = props;
    let btnClassName = "inline-flex items-center rounded border border-transparent bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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

export default PrimaryButton;
