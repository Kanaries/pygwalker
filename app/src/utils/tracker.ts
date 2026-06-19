type AnalyticsClient = {
    track: (eventName: string, data: Record<string, unknown>) => void;
};

type SegmentWindow = Window & {
    analytics?: AnalyticsClient;
};

const SEGMENT_WRITE_KEY = '9gxTNvl6Pl4WaZ5aymeHEBqNN8K4Op0U';
const SEGMENT_SCRIPT_ID = 'pygwalker-segment-analytics';

const initTracker = () => {
    let userId = "";
    let open = false;
    let analytics: AnalyticsClient | undefined;
    let loadPromise: Promise<void> | undefined;

    const setUserId = (id: string) => {
        userId = id;
    };

    const loadAnalytics = () => {
        if (analytics || loadPromise) {
            return;
        }

        loadPromise = new Promise<void>((resolve, reject) => {
            const win = window as SegmentWindow;
            const existing = document.getElementById(SEGMENT_SCRIPT_ID) as HTMLScriptElement | null;
            if (win.analytics) {
                analytics = win.analytics;
                resolve();
                return;
            }
            if (existing) {
                existing.addEventListener("load", () => resolve(), { once: true });
                existing.addEventListener(
                    "error",
                    () => reject(new Error("Failed to load Segment analytics")),
                    { once: true }
                );
                return;
            }

            const script = document.createElement("script");
            script.id = SEGMENT_SCRIPT_ID;
            script.async = true;
            script.src = `https://cdn.segment.com/analytics.js/v1/${SEGMENT_WRITE_KEY}/analytics.min.js`;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error("Failed to load Segment analytics"));
            document.head.appendChild(script);
        })
            .then(() => {
                const win = window as SegmentWindow;
                if (open && win.analytics) {
                    analytics = win.analytics;
                }
            })
            .catch(() => {
                analytics = undefined;
            })
            .finally(() => {
                loadPromise = undefined;
            });
    };

    const setOpen = (value: boolean) => {
        if (value === open) {
            return;
        }
        open = value;
        if (!open) {
            analytics = undefined;
            return;
        }
        loadAnalytics();
    }

    const track = (eventName: string, data: any) => {
        if (open && analytics) {
            analytics.track(eventName, {...data, userId});
        }
    };

    return {
        setUserId,
        setOpen,
        track
    }
}

export const tracker = initTracker();
