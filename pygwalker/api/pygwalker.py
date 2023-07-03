from typing import List, Dict, Any, Optional, Union
import html as m_html
import os

from typing_extensions import Literal
import ipywidgets

from pygwalker_utils.config import get_config
from pygwalker.utils.display import display_html, display_on_streamlit
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas
)
from pygwalker.services.upload_data import (
    BatchUploadDatasToolOnWidgets
)
from pygwalker.services.spec import get_spec_json
from pygwalker.communications.hacker_comm import HackerCommunication, BaseCommunication
from pygwalker import __version__, __hash__


class PygWalker:
    """PygWalker"""
    def __init__(
        self,
        gid: Optional[Union[int, str]],
        origin_data_source: List[Dict[str, Any]],
        field_specs: Dict[str, Any],
        spec: str,
        source_invoke_code: str,
        hidedata_source_config: bool,
        theme_key: Literal['vega', 'g2'],
        dark: Literal['media', 'light', 'dark'],
        **kwargs
    ):
        if gid is None:
            self.gid = GlobalVarManager.get_global_gid()
        else:
            self.gid = gid
        self.origin_data_source = origin_data_source
        self.field_specs = field_specs
        self.spec = spec
        self.source_invoke_code = source_invoke_code
        self.hidedata_source_config = hidedata_source_config
        self.theme_key = theme_key
        self.dark = dark
        self.data_source_id = rand_str()
        self.other_props = kwargs
        self.vis_spec, self.spec_type = get_spec_json(spec)

    def to_html(self) -> str:
        props = self._get_props()
        return self._get_render_iframe(props)

    def display_on_streamlit(self):
        display_on_streamlit(self.to_html())

    def display_on_jupyter(self):
        """
        Display on jupyter notebook/lab.
        Since `display_on_jupyter_use_widgets` is used instead, this function is only used when sharing.
        If share has large data loading, only sample data can be displayed.
        After that, it will be changed to python for data calculation,
        and only a small amount of data will be output to the front end to complete the analysis of big data.
        """
        data_source = get_max_limited_datas(self.origin_data_source)
        props = self._get_props(data_source)
        iframe_html = self._get_render_iframe(props)

        display_html(iframe_html)

    def display_on_jupyter_use_widgets(self):
        """
        use ipywidgets, Display on jupyter notebook/lab.
        When the kernel is down, the chart will not be displayed, so use `display_on_jupyter` to share
        """
        comm = HackerCommunication(self.gid)
        data_source = get_max_limited_datas(self.origin_data_source)
        props = self._get_props(
            "jupyter",
            data_source,
            len(self.origin_data_source) > len(data_source)
        )
        iframe_html = self._get_render_iframe(props)

        html_widgets = ipywidgets.Box(
            [ipywidgets.HTML(iframe_html), comm.get_widgets()],
            layout=ipywidgets.Layout(display='block')
        )

        self._init_callback(comm)

        display_html(html_widgets)

    def _init_callback(self, comm: BaseCommunication):
        upload_tool = BatchUploadDatasToolOnWidgets(comm)

        def reuqest_data_callback(_):
            upload_tool.run(
                records=self.origin_data_source,
                sample_data_count=0,
                data_source_id=self.data_source_id
            )
            return {}

        def get_latest_vis_spec(_):
            vis_spec, _ = get_spec_json(self.spec)
            return {"visSpec": vis_spec}

        def update_spec(data: Dict[str, Any]):
            with open(self.spec, "w", encoding="utf-8") as f:
                f.write(data["content"])

        comm.register("request_data", reuqest_data_callback)
        comm.register("get_latest_vis_spec", get_latest_vis_spec)
        comm.register("update_vis_spec", update_spec)

    def _get_props(
        self,
        env: str = "",
        data_source: Optional[Dict[str, Any]] = None,
        need_load_datas: bool = False
    ) -> Dict[str, Any]:
        if data_source is None:
            data_source = self.origin_data_source
        return {
            "id": self.gid,
            "dataSource": data_source,
            "len": len(data_source),
            "version": __version__,
            "hashcode": __hash__,
            "userConfig": get_config()[0],
            "visSpec": self.vis_spec,
            "rawFields": self.field_specs,
            "hideDataSourceConfig": self.hidedata_source_config,
            "fieldkeyGuard": False,
            "themeKey": self.theme_key,
            "sourceInvokeCode": self.source_invoke_code,
            "dataSourceProps": {
                'tunnelId': 'tunnel!',
                'dataSourceId': self.data_source_id,
            },
            "env": env,
            "specType": self.spec_type,
            "needLoadDatas": need_load_datas,
            **self.other_props,
        }

    def _get_render_iframe(self, props: Dict[str, Any]) -> str:
        html = render_gwalker_html(self.gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(self.gid, srcdoc)
