from typing import Dict, Any, List
import html as m_html
import os

from jinja2 import Environment, PackageLoader

from pygwalker._constants import ROOT_DIR
from pygwalker.utils.display import display_html


jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def _render_preview_html(*, images: List[str], row_count: int, col_count: int, div_id: str, title: str) -> str:
    image_list = [[None] * col_count for _ in range(row_count)]
    for image in images:
        image_list[image["rowIndex"]][image["colIndex"]] = image

    with open(os.path.join(ROOT_DIR, 'templates', 'tailwind.js'), 'r', encoding='utf-8') as f:
        tailwind_js = f.read()

    html = jinja_env.get_template("preview.html").render(
        tailwind_js=tailwind_js,
        image_list=image_list,
        div_id=div_id,
        title=title
    )

    iframe = jinja_env.get_template("preview_iframe.html").render(
        iframe_id=div_id,
        srcdoc=m_html.escape(html)
    )

    return iframe


class PreviewImageTool:
    """Preview image tool for pygwalker"""
    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"

    def init_display(self):
        display_html("", slot_id=self.image_slot_id)

    def render(self, datas: Dict[str, Any]):
        html = _render_preview_html(
            images=datas["charts"],
            row_count=datas["nRows"],
            col_count=datas["nCols"],
            title=datas["title"],
            div_id=self.image_slot_id
        )
        display_html(html, slot_id=self.image_slot_id)
