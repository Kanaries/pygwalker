import { AnalyticsBrowser } from '@segment/analytics-next'


const initTracker = () => {
    let userId = "";
    let open = false;
    let analytics: ReturnType<typeof AnalyticsBrowser.load> | undefined;

    const setUserId = (id: string) => {
        userId = id;
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
        analytics = AnalyticsBrowser.load({ writeKey: '9gxTNvl6Pl4WaZ5aymeHEBqNN8K4Op0U' });
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
