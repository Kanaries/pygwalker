from typing import List, Dict, Any, Optional, Union
import html as m_html
import time

from typing_extensions import Literal

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
    BatchUploadDatasToolOnJupyter
)
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
        theme_key: Literal['vega', 'g2'] = 'g2',
        dark: Literal['media', 'light', 'dark'] = 'media',
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

        if len(self.origin_data_source) > len(props["dataSource"]):
            upload_tool = BatchUploadDatasToolOnJupyter()
            upload_tool.init()
            display_html(iframe_html)
            time.sleep(1)
            upload_tool.run(
                records=self.origin_data_source,
                sample_data_count=len(props["dataSource"]),
                data_source_id=props["dataSourceProps"]["dataSourceId"],
                gid=self.gid,
                tunnel_id=props["dataSourceProps"]["tunnelId"],
            )
        else:
            display_html(iframe_html)

    def display_on_jupyter_use_widgets(self):
        pass

    def _get_props(self, data_source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if data_source is None:
            data_source = self.origin_data_source
        return {
            "id": self.gid,
            "dataSource": data_source,
            "len": len(data_source),
            "version": __version__,
            "hashcode": __hash__,
            "userConfig": get_config()[0],
            "visSpec": self.spec,
            "rawFields": self.field_specs,
            "hideDataSourceConfig": self.hidedata_source_config,
            "fieldkeyGuard": False,
            "themeKey": self.theme_key,
            "sourceInvokeCode": self.source_invoke_code,
            "dataSourceProps": {
                'tunnelId': 'tunnel!',
                'dataSourceId': self.data_source_id,
            },
            **self.other_props,
        }

    def _get_render_iframe(self, props: Dict[str, Any]) -> str:
        html = render_gwalker_html(self.gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(self.gid, srcdoc)
