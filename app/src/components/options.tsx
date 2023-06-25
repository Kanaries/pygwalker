import React, { useEffect, useState } from "react";
import type { IAppProps } from "../interfaces";

const copyToClipboard = async (text: string) => {
    return navigator.clipboard.writeText(text);
};

interface ISolutionProps {
    header: string;
    cmd: string;
}

const updateSolutions: ISolutionProps[] = [
    {
        header: "Using pip:",
        cmd: "pip install pygwalker --upgrade",
    },
    {
        header: "Using anaconda:",
        cmd: "conda install -c conda-forge pygwalker",
    },
];

const Solution: React.FC<ISolutionProps> = (props) => {
    const [busy, setBusy] = useState(false);

    return (
        <>
            <header>{props.header}</header>
            <div>
                <code>{props.cmd}</code>
                <div
                    role="button"
                    aria-label="Copy command"
                    tabIndex={0}
                    aria-disabled={busy}
                    onClick={() => {
                        if (busy) {
                            return;
                        }
                        setBusy(true);
                        copyToClipboard(props.cmd).finally(() => {
                            setTimeout(() => {
                                setBusy(false);
                            }, 2_000);
                        });
                    }}
                >
                    <small>{busy ? "Copied" : "Copy"}</small>
                    <span>{busy ? "\u2705" : "\u274f"}</span>
                </div>
            </div>
        </>
    );
};

const RAND_HASH = Math.random().toString(16).split(".").at(1);
const Options: React.FC<IAppProps> = (props: IAppProps) => {
    const [outdated, setOutDated] = useState<Boolean>(false);
    const [appMeta, setAppMeta] = useState<any>({});
    const [showUpdateHint, setShowUpdateHint] = useState(false);
    const UPDATE_URL = "https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates";
    const VERSION = (window as any)?.__GW_VERSION || "current";
    const HASH = (window as any)?.__GW_HASH || RAND_HASH;
    useEffect(() => {
        if (props.userConfig?.privacy !== "offline") {
            const req = `${UPDATE_URL}?pkg=pygwalker-app&v=${VERSION}&hashcode=${HASH}&env=${process.env.NODE_ENV}`;
            fetch(req, {
                headers: {
                    "Content-Type": "application/json",
                },
            })
                .then((resp) => resp.json())
                .then((res) => {
                    setAppMeta({ data: res.data });
                    setOutDated(res?.data?.outdated || false);
                });
        }
    }, []);

    useEffect(() => {
        setShowUpdateHint(false);
    }, [outdated]);

    useEffect(() => {
        if (!showUpdateHint) {
            return;
        }
        const handleDismiss = () => {
            setShowUpdateHint(false);
        };
        document.addEventListener("click", handleDismiss);
        return () => {
            document.removeEventListener("click", handleDismiss);
        };
    }, [showUpdateHint]);

    useEffect(() => {
        setShowUpdateHint(false);
    }, [outdated]);

    useEffect(() => {
        if (!showUpdateHint) {
            return;
        }
        const handleDismiss = () => {
            setShowUpdateHint(false);
        };
        document.addEventListener("click", handleDismiss);
        return () => {
            document.removeEventListener("click", handleDismiss);
        };
    }, [showUpdateHint]);

    return (
        <>
            <style>{`
        .update_link {
            position: fixed;
            right: 2rem;
            top: 2rem;
            background-color: rgba(56,189,248,.1);
            color: rgb(2, 132, 199);
            margin-top: 50px;
            --line-height: 1.25rem;
            line-height: var(--line-height);
            --padding-block: 0.25rem;
            padding: var(--padding-block) 0.75rem;
            border-radius: calc(var(--padding-block) + var(--line-height) * .5);
            font-weight: 500;
            font-size: .75rem;
            font-family: sans-serif;
            text-align: end;
        }
        .update_link p {
            margin: 0;
            padding: 0;
        }
        .update_link *[role="button"] {
            cursor: pointer;
        }
        .update_link *[role="separator"] {
            user-select: none;
            margin-inline: 0.5em;
            display: inline-block;
        }
        .update_link .solutions {
            margin: 1em 0 1em 2em;
            display: grid;
            grid-template-columns: repeat(2, auto);
            gap: 0.2em 0.8em;
            font-family: monospace;
        }
        .update_link .solutions > * {
            display: flex;
            align-items: center;
        }
        .update_link .solutions div:has(> code) {
            display: flex;
            align-items: center;
            background-color: #777;
            color: #eee;
            padding-inline: 0.8em 6em;
            padding-block: 0.1em;
            border-radius: 2px;
            position: relative;
            height: 2em;
        }
        .update_link *[aria-disabled="true"] {
            opacity: 1 !important;
            cursor: default !important;
        }
        .update_link .solutions div *[role="button"] {
            user-select: none;
            flex-grow: 0;
            flex-shrink: 0;
            cursor: pointer;
            margin-left: 1em;
            background-color: #eee;
            color: #444;
            padding-inline: 0.4em;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            border-radius: 1em;
            opacity: 0.5;
            position: absolute;
            right: 0.5em;
            z-index: 10;
            font-family: 
        }
        .update_link .solutions div:hover *[role="button"] {
            opacity: 1;
        }
        .update_link .solutions div *[role="button"] > small {
            font-size: 0.65rem;
            margin-right: 0.5em;
        }
        .update_link .solutions div > code {
            flex-grow: 1;
            flex-shrink: 1;
            text-align: start;
        }
        .update_link a {
            font-family: monospace;
            color: inherit;
            text-decoration: none;
            cursor: pointer;
        }
        .update_link a span {
            filter: brightness(1.8);
        }
        .update_link p span {
            font-family: monospace;
            color: inherit;
        }
        @media (prefers-color-scheme: dark) {
            .update_link span, .update_link header, .update_link a {
                filter: brightness(1.5);
            }
        }
    `}</style>
            {outdated && (
                <div className="update_link" aria-live="assertive" role="alert" tabIndex={0} onClick={(e) => e.stopPropagation()}>
                    <p>
                        <a href="https://pypi.org/project/pygwalker" target="_blank">
                            {"Update: "}
                            {`${VERSION}\u2191`}
                            <span>{` ${appMeta?.data?.latest?.release?.version || "latest"}`}</span>
                        </a>
                        <span role="separator">|</span>
                        <span aria-haspopup role="button" tabIndex={0} onClick={() => setShowUpdateHint((s) => !s)}>
                            {`${showUpdateHint ? "Hide" : " Cmd"} \u274f`}
                        </span>
                    </p>
                    {showUpdateHint && (
                        <div className="solutions">
                            {updateSolutions.map((sol, i) => (
                                <Solution key={i} {...sol} />
                            ))}
                        </div>
                    )}
                </div>
            )}
        </>
    );
};
export default Options;
