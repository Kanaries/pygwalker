import { Fragment, useState, createContext, useCallback, ReactElement, useContext } from "react";
import { Transition } from "@headlessui/react";
import { CheckCircleIcon } from "@heroicons/react/24/outline";
import { XMarkIcon } from "@heroicons/react/20/solid";

export interface INotification {
    title: string;
    message: string;
    type: "success" | "error" | "info" | "warning";
}

const NotificationContext = createContext<{ notify: (not: INotification, t: number) => void }>(null!);

export function useNotification() {
    return useContext(NotificationContext);
}

function getNotificationIcon(type: INotification["type"]) {
    switch (type) {
        case "success":
            return <CheckCircleIcon className="h-6 w-6 text-green-400" aria-hidden="true" />;
        case "error":
            return <XMarkIcon className="h-6 w-6 text-red-400" aria-hidden="true" />;
        case "info":
            return <CheckCircleIcon className="h-6 w-6 text-blue-400" aria-hidden="true" />;
        case "warning":
            return <CheckCircleIcon className="h-6 w-6 text-yellow-400" aria-hidden="true" />;
    }
}

const NotificationWrapper: React.FC<{ children: ReactElement }> = (props) => {
    const [show, setShow] = useState(false);
    const [notification, setNotification] = useState<INotification | null>(null);

    const notify = useCallback((not: INotification, t: number) => {
        setShow(true);
        setNotification(not);
        setTimeout(() => {
            setShow(false);
        }, t);
    }, []);

    return (
        <NotificationContext.Provider value={{ notify }}>
            {props.children}
            {/* Global notification live region, render this permanently at the end of the document */}
            {notification && (
                <div aria-live="assertive" className="pointer-events-none fixed inset-0 flex items-end px-4 py-6 sm:items-start sm:p-6 z-[999]">
                    <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
                        {/* Notification panel, dynamically insert this into the live region when it needs to be displayed */}
                        <Transition
                            show={show}
                            as={Fragment}
                            enter="transform ease-out duration-300 transition"
                            enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
                            enterTo="translate-y-0 opacity-100 sm:translate-x-0"
                            leave="transition ease-in duration-100"
                            leaveFrom="opacity-100"
                            leaveTo="opacity-0"
                        >
                            <div className="pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg bg-zinc-700 shadow-lg ring-1 ring-black ring-opacity-5">
                                <div className="p-4">
                                    <div className="flex items-start">
                                        <div className="flex-shrink-0">
                                            {getNotificationIcon(notification.type)}
                                        </div>
                                        <div className="ml-3 w-0 flex-1 pt-0.5">
                                            <p className="text-sm font-medium text-gray-50">{notification.title}</p>
                                            <p className="mt-1 text-sm text-gray-300">{notification.message}</p>
                                        </div>
                                        <div className="ml-4 flex flex-shrink-0">
                                            <button
                                                type="button"
                                                className="inline-flex rounded-md bg-zinc-900 text-gray-400 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                                onClick={() => {
                                                    setShow(false);
                                                }}
                                            >
                                                <span className="sr-only">Close</span>
                                                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Transition>
                    </div>
                </div>
            )}
        </NotificationContext.Provider>
    );
};

export default NotificationWrapper;
