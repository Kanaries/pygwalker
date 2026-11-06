import React, { Suspense, useCallback, useContext, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { observer } from 'mobx-react-lite';
import type { IDarkMode } from '@kanaries/graphic-walker/interfaces';
import { SunIcon, MoonIcon, DesktopIcon } from '@radix-ui/react-icons';
import { ToggleGroup, ToggleGroupItem } from '../components/ui/toggle-group';
import commonStore from '../store/common';
import { AppContext } from '../store/context';
import { currentMediaTheme } from '../utils/theme';

// @ts-ignore
import style from '../index.css?inline';

const InitModal = React.lazy(() => import("../components/initModal"));

export type IPygWalkerTheme = React.CSSProperties & {
    [name: `--${string}`]: string | number | undefined;
};

// Graphic Walker already owns a shadow root. Slot it into our isolated shell from
// the light DOM: its modal library can only resolve one shadow boundary to document.body.
const hostContainerContext = React.createContext<HTMLElement | null>(null);
const HostShadowSlot = ({ children }: { children: React.ReactNode }) => {
    const container = useContext(hostContainerContext);
    const name = React.useId();
    const [target, setTarget] = useState<HTMLDivElement | null>(null);
    React.useLayoutEffect(() => {
        if (!container) return;
        const element = document.createElement('div');
        element.slot = name;
        container.append(element);
        setTarget(element);
        return () => element.remove();
    }, [container, name]);
    if (!container) return <>{children}</>;
    return <slot name={name}>{target && createPortal(children, target)}</slot>;
};

const MainApp = observer((props: {children: React.ReactNode, darkMode: "dark" | "light" | "media", hideToolBar?: boolean, gid?: string, sendMessage?: boolean, theme?: IPygWalkerTheme}) => {
    const [portal, setPortal] = useState<HTMLDivElement | null>(null);
    const [selectedDarkMode, setSelectedDarkMode] = useState(props.darkMode);
    const [darkMode, setDarkMode] = useState(currentMediaTheme(props.darkMode));

    useEffect(() => {
        setSelectedDarkMode(props.darkMode);
    }, [props.darkMode]);

    const sendAppearanceMessageToParent = useCallback((appearance: IDarkMode) => {
        if (!props.sendMessage) return;
        window.parent.postMessage({
            action: "changeAppearance",
            gid: props.gid,
            appearance: appearance
        }, "*");
    }, [props.gid, props.sendMessage]);

    useEffect(() => {
        if (selectedDarkMode === "media") {
            setDarkMode(currentMediaTheme(selectedDarkMode));
            sendAppearanceMessageToParent(currentMediaTheme(selectedDarkMode));
            const media = window.matchMedia('(prefers-color-scheme: dark)');
            const listener = (e: MediaQueryListEvent) => {
                setDarkMode(e.matches ? "dark" : "light");
            }
            media.addEventListener("change", listener);
            return () => media.removeEventListener("change", listener);
        } else {
            sendAppearanceMessageToParent(selectedDarkMode);
            setDarkMode(selectedDarkMode);
        }
    }, [selectedDarkMode])

    return (
        <AppContext
            portalContainerContext={portal}
            darkModeContext={darkMode}
        >
            <div
                className={`${darkMode === "dark" ? "dark": ""} bg-background text-foreground`}
                style={props.theme}
            >
                <div className="p-2">
                    <style>{style}</style>
                    <div className='overflow-y-auto'>
                        { props.children }
                    </div>
                    {!props.hideToolBar && (
                        <div className="flex w-full mt-1 p-1 overflow-hidden border-t border-border">
                            <ToggleGroup
                                type="single"
                                value={selectedDarkMode}
                                onValueChange={(value) => {value && setSelectedDarkMode(value as IDarkMode)}}
                            >
                                <ToggleGroupItem value="dark">
                                    <MoonIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                                <ToggleGroupItem value="light">
                                    <SunIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                                <ToggleGroupItem value="media">
                                    <DesktopIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                            </ToggleGroup>
                        </div>
                    )}
                    {commonStore.initModalOpen && (
                        <Suspense fallback={null}>
                            <InitModal />
                        </Suspense>
                    )}
                    <div ref={setPortal}></div>
                </div>
            </div>
        </AppContext>
    )
})

export { MainApp, HostShadowSlot, hostContainerContext };
