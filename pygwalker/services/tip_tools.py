from threading import Thread
import time

from pygwalker.utils.display import display_html

WIDGETS_TIPS = """
<div style="">
If you are using pygwalker in a local notebook (not jupyter lab) environment, please run `pip install "pygwalker[notebook]" --pre` to ensure that pygwalker can be used normally.(close after 30 seconds)
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
        time.sleep(30)
        display_html("", slot_id=self.slot_id)
