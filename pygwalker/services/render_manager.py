from typing import Any, Dict, Optional

from duckdb import ParserException

from pygwalker.services.preview_image import render_gw_chart_preview_html, render_gw_preview_html
from pygwalker.services.render import render_gwalker_html, render_gwalker_iframe
from pygwalker.utils.randoms import rand_str


class RenderManager:
    """Render walker iframe and preview HTML fragments."""

    def __init__(self, walker):
        self.walker = walker

    def get_render_iframe(
        self,
        props: Dict[str, Any],
        return_iframe: bool = True,
        iframe_width: Optional[str] = None,
        iframe_height: Optional[str] = None,
    ) -> str:
        html = render_gwalker_html(self.walker.gid, props)
        if return_iframe:
            return render_gwalker_iframe(
                self.walker.gid,
                html,
                iframe_width,
                iframe_height,
                self.walker.appearance,
            )
        return html

    def get_preview_html(self, manual: bool = False) -> str:
        if not self.walker.workflow_list:
            return ""
        datas = []
        for workflow in self.walker.workflow_list:
            try:
                datas.append(self.walker.data_parser.get_datas_by_payload(workflow))
            except ParserException:
                datas.append([])
        return render_gw_preview_html(
            self.walker.vis_spec,
            datas,
            self.walker.theme_key,
            self.walker.gid if not manual else self.walker.gid + rand_str(),
            self.walker.appearance,
        )

    def get_chart_preview_html(self, chart_name: int, title: str, desc: str) -> str:
        chart_index = self.walker.spec_manager.get_chart_index(chart_name)

        if not self.walker.workflow_list:
            return ""
        data = self.walker.data_parser.get_datas_by_payload(self.walker.workflow_list[chart_index])
        return render_gw_chart_preview_html(
            single_vis_spec=self.walker.vis_spec[chart_index],
            data=data,
            theme_key=self.walker.theme_key,
            title=title,
            desc=desc,
            appearance=self.walker.appearance,
        )
