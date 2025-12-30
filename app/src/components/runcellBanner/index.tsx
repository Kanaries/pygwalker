import React, { useState } from "react";
import { tracker } from "@/utils/tracker";

const RUNCELL_LOGO_URL = "https://www.runcell.dev/runcell-logo.svg";
const RUNCELL_WEBSITE = "https://www.runcell.dev?utm_source=pygwalker";

const LLM_LOGOS = [
    "https://www.runcell.dev/llm-icons/openai.svg",
    "https://www.runcell.dev/llm-icons/claude-color.svg",
    "https://www.runcell.dev/llm-icons/gemini-color.svg",
    "https://www.runcell.dev/llm-icons/deepseek-color.svg",
];

interface RuncellBannerProps {
    env?: string;
}

const checkRuncellInstalled = (): boolean => {
    try {
        // Runcell JupyterLab plugin stores user status in localStorage
        const runcellUser = window.parent.localStorage.getItem("plugin_auth_user_v2");
        return runcellUser !== null;
    } catch {
        return false;
    }
};

export const RuncellBanner: React.FC<RuncellBannerProps> = ({ env }) => {
    const [dismissed, setDismissed] = useState(false);

    // Only show in Jupyter environments
    if (env !== "jupyter_widgets" && env !== "anywidget") {
        return null;
    }

    // Don't show if runcell is installed or user dismissed
    if (checkRuncellInstalled() || dismissed) {
        return null;
    }

    const  handleClick = () => {
        tracker.track("click", { entity: "runcell_banner" });
        window.open(RUNCELL_WEBSITE, "_blank");
    };

    const handleDismiss = (e: React.MouseEvent) => {
        e.stopPropagation();
        tracker.track("click", { entity: "runcell_banner_dismiss" });
        setDismissed(true);
    };

    return (
        <div
            className="flex items-center justify-between gap-3 px-4 py-2 mb-2 rounded-md bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30 border border-purple-200 dark:border-purple-800 cursor-pointer hover:shadow-md transition-shadow"
            onClick={handleClick}
        >
            <div className="flex items-center gap-3">
                <img
                    src={RUNCELL_LOGO_URL}
                    alt="Runcell"
                    className="w-6 h-6"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                    Enable AI Agent for data analysis with pip install runcell
                </span>
            </div>
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-white/80">
                    {LLM_LOGOS.map((logo, index) => (
                        <img
                            key={index}
                            src={logo}
                            alt="LLM"
                            className="w-4 h-4"
                        />
                    ))}
                </div>
                <button
                    onClick={handleDismiss}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-lg leading-none px-1"
                    aria-label="Dismiss"
                >
                    ×
                </button>
            </div>
        </div>
    );
};

export default RuncellBanner;
