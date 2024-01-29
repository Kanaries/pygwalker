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
