import { AnalyticsBrowser } from '@segment/analytics-next'


const initTracker = () => {
    var userId = "";
    var open = false;
    var analytics;

    const setUserId = (id: string) => {
        userId = id;
    };

    const setOpen = (value: boolean) => {
        if (value) {
            analytics = AnalyticsBrowser.load({ writeKey: '9gxTNvl6Pl4WaZ5aymeHEBqNN8K4Op0U' })
        }
        open = value;
    }

    const track = (eventName: string, data: any) => {
        if (open) {
            analytics.track(eventName, {...data, userId})
        }
    };

    return {
        setUserId,
        setOpen,
        track
    }
}

export const tracker = initTracker();
