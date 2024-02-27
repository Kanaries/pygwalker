import { createContext } from 'react';

import { composeContext } from "@/utils/context";

export const portalContainerContext = createContext<HTMLDivElement | null>(null);

export const darkModeContext = createContext<"dark" | "light">("light");

export const AppContext = composeContext({ portalContainerContext, darkModeContext });
