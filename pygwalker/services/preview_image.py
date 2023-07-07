from typing import Dict, Any

from pygwalker.utils.display import display_html
from .render import render_preview_html


class PreviewImageTool:
    """Preview image tool for pygwalker"""
    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"

    def init_display(self):
        display_html("", slot_id=self.image_slot_id)

    def render(self, datas: Dict[str, Any]):
        html = render_preview_html(
            datas["charts"],
            datas["nRows"],
            datas["nCols"],
            self.image_slot_id
        )
        display_html(html, slot_id=self.image_slot_id)
