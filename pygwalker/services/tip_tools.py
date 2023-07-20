from threading import Thread
import time

from pygwalker.utils.display import display_html

WIDGETS_TIPS = """
<div style="">
If you are using pygwalker on Jupyter Notebook(version<7) and it can't display properly, please execute code to fix it: `pip install "pygwalker[notebook]" --pre`.(close after 15 seconds)
<div>
"""

TIPS_MAP = {
    "widgets": WIDGETS_TIPS
}


class TipOnStartTool:
    """Tip on start tool for pygwalker"""

    def __init__(self, gid: str, tip_name: str):
        self.gid = gid
        self.slot_id = f"user-tips-{gid}"
        self.tips = TIPS_MAP.get(tip_name, "")
        Thread(target=self.hide).start()

    def show(self):
        display_html(self.tips, slot_id=self.slot_id)

    def hide(self):
        time.sleep(15)
        display_html("", slot_id=self.slot_id)
