import { zincTheme } from '@kanaries/graphic-walker';
import type { IColorSet, IUIThemeConfig } from '@kanaries/graphic-walker/interfaces';
import type { IPygWalkerTheme } from '../index';

/** Graphic Walker owns another shadow root and needs its palette through uiTheme. */
export function hostThemeToUITheme(theme: IPygWalkerTheme): IUIThemeConfig {
    const colors: Partial<IColorSet> = {};
    const tokens: (keyof IColorSet)[] = [
        'background', 'foreground', 'card', 'card-foreground', 'popover', 'popover-foreground',
        'primary', 'primary-foreground', 'secondary', 'secondary-foreground', 'muted', 'muted-foreground',
        'accent', 'accent-foreground', 'destructive', 'destructive-foreground', 'border', 'input', 'ring',
    ];
    for (const token of tokens) {
        const value = theme[`--${token}`];
        if (typeof value === 'string' && value.trim()) {
            colors[token] = `hsl(${value})`;
        }
    }
    // The host supplies its current palette and controls appearance for this mount.
    return {
        light: { ...zincTheme.light, ...colors },
        dark: { ...zincTheme.dark, ...colors },
    };
}

export function currentMediaTheme(dark: "dark" | "light" | "media"): "dark" | "light" {
    if (dark === "media") {
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return "dark";
        } else {
            return "light";
        }
    } else {
        return dark;
    }
}
