import React, { Context, ContextType } from 'react';

export function composeContext<T extends Record<string, Context<any>>>(contexts: T) {
    return function (
        props: { children?: React.ReactNode | Iterable<React.ReactNode> } & {
            [K in keyof T]: ContextType<T[K]>;
        }
    ) {
        let node = props.children;
        Object.keys(contexts).forEach((contextKey) => {
            const context = contexts[contextKey];
            node = <context.Provider value={props[contextKey]}>{node}</context.Provider>;
        });
        return node as JSX.Element;
    };
}
