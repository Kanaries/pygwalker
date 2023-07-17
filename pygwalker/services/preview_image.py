from typing import Optional, List

from jinja2 import Environment, PackageLoader
from pydantic import BaseModel, Field

from pygwalker.utils.display import display_html


jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


class ImgData(BaseModel):
    row_index: int = Field(..., alias="rowIndex")
    col_index: int = Field(..., alias="colIndex")
    data: str
    height: int
    width: int
    canvas_height: int = Field(..., alias="canvasHeight")
    canvas_width: int = Field(..., alias="canvasWidth")


class ChartData(BaseModel):
    charts: List[ImgData]
    single_chart: str = Field(..., alias="singleChart")
    n_rows: int = Field(..., alias="nRows")
    n_cols: int = Field(..., alias="nCols")
    title: str


def render_preview_html(
    chart_data: ChartData,
    div_id: str,
    *,
    custom_title: Optional[str] = None,
    desc: str = "",
) -> str:
    image_list = [[None] * chart_data.n_cols for _ in range(chart_data.n_rows)]
    for image in chart_data.charts:
        image_list[image.row_index][image.col_index] = image

    html = jinja_env.get_template("preview.html").render(
        image_list=image_list,
        div_id=div_id,
        title=custom_title if custom_title is not None else chart_data.title,
        desc=desc,
    )

    return html


class PreviewImageTool:
    """Preview image tool for pygwalker"""
    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"

    def init_display(self):
        display_html("", slot_id=self.image_slot_id)

    def render(self, chart_data: ChartData):
        html = render_preview_html(
            chart_data=chart_data,
            div_id=self.image_slot_id
        )
        display_html(html, slot_id=self.image_slot_id)
