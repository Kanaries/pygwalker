from typing import Union

from IPython.display import display, HTML
import ipywidgets

DISPLAY_HANDLER = {}


def display_html(
    html: Union[str, HTML, ipywidgets.Widget],
    *,
    slot_id: str = None
):
    """Judge the presentation method to be used based on the context

    Args:
        - html (str): html string to display.
        - env: (Literal['Widgets' | 'Streamlit' | 'Jupyter'], optional): The enviroment using pygwalker
        *
        - slot_id(str): display with given id.
    """
    if isinstance(html, str):
        widget = HTML(html)
    else:
        widget = html

    if slot_id is None:
        display(widget)
    else:
        handler = DISPLAY_HANDLER.get(slot_id)
        if handler is None:
            handler = display(widget, display_id=slot_id)
            DISPLAY_HANDLER[slot_id] = handler
        else:
            handler.update(widget)
