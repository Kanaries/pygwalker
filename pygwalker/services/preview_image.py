from typing import Dict, Any, Optional

from jinja2 import Environment, PackageLoader

from pygwalker.utils.display import display_html


jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def render_preview_html(
    datas: Dict[str, Any],
    div_id: str,
    *,
    custom_title: Optional[str] = None,
    desc: str = "",
) -> str:
    """
    datas: {
        "charts": {"rowIndex": int, ""colIndex": int, "data": str, "height": int, "width": int, "canvasHeight": int, "canvasWidth": int},
        "nRows": int,
        "nCols": int,
        "title": str
    }
    """
    image_list = [[None] * datas["nCols"] for _ in range(datas["nRows"])]
    for image in datas["charts"]:
        image_list[image["rowIndex"]][image["colIndex"]] = image

    html = jinja_env.get_template("preview.html").render(
        image_list=image_list,
        div_id=div_id,
        title=custom_title if custom_title is not None else datas["title"],
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

    def render(self, datas: Dict[str, Any]):
        html = render_preview_html(
            datas=datas,
            div_id=self.image_slot_id
        )
        display_html(html, slot_id=self.image_slot_id)
