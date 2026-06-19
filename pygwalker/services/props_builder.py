from typing import Any, Callable, Dict, Optional

from pygwalker import __version__
from pygwalker.services.global_var import GlobalVarManager


class PropsBuilder:
    """Build frontend props for a walker without owning rendering or tracking."""

    def __init__(self, walker, get_user_id: Callable[[], str]):
        self.walker = walker
        self.get_user_id = get_user_id

    def build(
        self,
        env: str = "",
        data_source: Optional[Dict[str, Any]] = None,
        need_load_datas: bool = False,
    ) -> Dict[str, Any]:
        if data_source is None:
            data_source = self.walker.origin_data_source
        return {
            "id": self.walker.gid,
            "dataSource": data_source,
            "len": len(data_source),
            "version": __version__,
            "hashcode": self.get_user_id(),
            "userConfig": {
                "privacy": GlobalVarManager.privacy,
            },
            "visSpec": self.walker.vis_spec,
            "rawFields": [{**field, "offset": 0} for field in self.walker.field_specs],
            "fieldkeyGuard": False,
            "themeKey": self.walker.theme_key,
            "dark": self.walker.appearance,
            "sourceInvokeCode": self.walker.source_invoke_code,
            "dataSourceProps": {
                "tunnelId": self.walker.tunnel_id,
                "dataSourceId": self.walker.data_source_id,
            },
            "env": env,
            "specType": self.walker.spec_type,
            "needLoadDatas": not self.walker.kernel_computation and need_load_datas,
            "showCloudTool": self.walker.show_cloud_tool,
            "enableAskViz": GlobalVarManager.enable_askviz,
            "enableVlChat": GlobalVarManager.enable_vlchat,
            "needInitChart": not self.walker._chart_map,
            "useKernelCalc": self.walker.kernel_computation,
            "useSaveTool": self.walker.use_save_tool,
            "parseDslType": self.walker.parse_dsl_type,
            "gwMode": self.walker.gw_mode,
            "needLoadLastSpec": True,
            "datasetType": self.walker.dataset_type,
            "extraConfig": self.walker.other_props,
            "fieldMetas": self.walker.data_parser.field_metas,
            "isExportDataFrame": self.walker.is_export_dataframe,
            "defaultTab": self.walker.default_tab,
            "useCloudCalc": self.walker.cloud_computation,
        }
