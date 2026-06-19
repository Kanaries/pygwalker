import base64
import urllib.request
from typing import Any, Callable, Dict, Optional

from pygwalker.services.preview_image import render_gw_chart_preview_html
from pygwalker.utils.dsl_transform import dsl_to_workflow


class ChartExportManager:
    """Export and display saved chart previews for a walker."""

    def __init__(self, walker, display_fn: Callable[[Any], None]):
        self.walker = walker
        self.display_fn = display_fn

    def save_chart_to_file(self, chart_name: str, path: str, save_type: str = "png") -> None:
        if save_type == "html":
            content = self.export_chart_html(chart_name)
            write_mode = "w"
            encoding = "utf-8"
        elif save_type == "png":
            content = self.export_chart_png(chart_name)
            write_mode = "wb"
            encoding = None
        elif save_type == "svg":
            content = self.export_chart_svg(chart_name)
            write_mode = "wb"
            encoding = None
        else:
            raise ValueError(f"save_type must be html, png or svg, but got {save_type}")

        with open(path, write_mode, encoding=encoding) as f:
            f.write(content)

    def export_chart_html(self, chart_name: str) -> str:
        return self.walker._get_gw_chart_preview_html(chart_name, title="", desc="")

    def export_chart_png(self, chart_name: str) -> bytes:
        chart_data = self.walker._get_chart_by_name(chart_name)

        with urllib.request.urlopen(chart_data.single_chart) as png_string:
            return png_string.read()

    def export_chart_svg(self, chart_name: str) -> bytes:
        chart_data = self.walker._get_chart_by_name(chart_name)
        if len(chart_data.charts) == 0:
            raise ValueError(f"chart_name: {chart_name} has no svg data")
        svg_str = chart_data.charts[0].data
        prefix = "data:image/svg+xml;base64,"
        if isinstance(svg_str, str) and svg_str.startswith(prefix):
            return base64.b64decode(svg_str[len(prefix) :])
        if isinstance(svg_str, str):
            return svg_str.encode("utf-8")
        return svg_str

    def display_chart(self, chart_name: str, *, title: Optional[str] = None, desc: str = "") -> None:
        if title is None:
            title = chart_name

        html = self.walker._get_gw_chart_preview_html(chart_name, title=title, desc=desc)
        self.display_fn(html)

    def get_single_chart_html_by_spec(
        self,
        *,
        spec: Dict[str, Any],
        title: str = "",
        desc: str = "",
    ) -> str:
        workflow = dsl_to_workflow(spec)
        data = self.walker.data_parser.get_datas_by_payload(workflow)
        return render_gw_chart_preview_html(
            single_vis_spec=spec,
            data=data,
            theme_key=self.walker.theme_key,
            title=title,
            desc=desc,
            appearance=self.walker.appearance,
        )
