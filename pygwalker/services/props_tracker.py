from typing import Any, Callable, Dict


class PropsTracker:
    """Track frontend props invocations without owning props construction."""

    TRACKED_FIELDS = {
        "id",
        "version",
        "hashcode",
        "themeKey",
        "dark",
        "env",
        "specType",
        "needLoadDatas",
        "showCloudTool",
        "useKernelCalc",
        "useSaveTool",
        "parseDslType",
        "gwMode",
        "datasetType",
        "defaultTab",
        "useCloudCalc",
    }

    def __init__(self, walker, track_fn: Callable[[str, Dict[str, Any]], None]):
        self.walker = walker
        self.track_fn = track_fn

    def track_invocation(self, props: Dict[str, Any]) -> None:
        event_info = {key: value for key, value in props.items() if key in self.TRACKED_FIELDS}
        event_info["hasKanariesToken"] = bool(getattr(self.walker, "kanaries_api_key", ""))
        self.track_fn("invoke_props", event_info)
