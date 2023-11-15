import { Fragment } from "react";
import { Transition } from "@headlessui/react";
import { CheckCircleIcon } from "@heroicons/react/24/outline";
import { XMarkIcon } from "@heroicons/react/20/solid";
import commonStore, { INotification } from "../store/common";
import { observer } from "mobx-react-lite";

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

const Notification: React.FC = observer(() => {
    return (
        <div>
            {commonStore.notification && (
                <div aria-live="assertive" className="pointer-events-none fixed inset-0 flex items-end px-4 py-6 sm:items-start sm:p-6 z-[25539]">
                    <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
                        {/* Notification panel, dynamically insert this into the live region when it needs to be displayed */}
                        <Transition
                            show={commonStore.notification != null}
                            as={Fragment}
                            enter="transform ease-out duration-300 transition"
                            enterFrom="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
                            enterTo="translate-y-0 opacity-100 sm:translate-x-0"
                            leave="transition ease-in duration-100"
                            leaveFrom="opacity-100"
                            leaveTo="opacity-0"
                        >
                            <div className="pointer-events-auto w-full max-w-md overflow-hidden rounded-lg bg-zinc-700 shadow-lg ring-1 ring-black ring-opacity-5">
                                <div className="p-4">
                                    <div className="flex items-start">
                                        <div className="flex-shrink-0">
                                            {getNotificationIcon(commonStore.notification.type)}
                                        </div>
                                        <div className="ml-3 w-0 flex-1 pt-0.5">
                                            <p className="text-sm font-medium text-gray-50">{commonStore.notification.title}</p>
                                            <p className="mt-1 text-sm text-gray-300">{commonStore.notification.message}</p>
                                        </div>
                                        <div className="ml-4 flex flex-shrink-0">
                                            <button
                                                type="button"
                                                className="inline-flex rounded-md bg-zinc-900 text-gray-400 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                                onClick={() => {
                                                    commonStore.setNotification(null);
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
        </div>
    );
});

export default Notification;
