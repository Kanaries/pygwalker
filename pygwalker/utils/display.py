from typing_extensions import Literal

from IPython.display import display, HTML

DISPLAY_HANDLER = {}


def display_html(
    html: str,
    env: Literal['Jupyter', 'Streamlit', 'Widgets'] = 'Jupyter',
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
    if env == 'Jupyter':
        if slot_id is None:
            display(HTML(html))
        else:
            handler = DISPLAY_HANDLER.get(slot_id)
            if handler is None:
                handler = display(HTML(html), display_id=slot_id)
                DISPLAY_HANDLER[slot_id] = handler
            else:
                handler.update(HTML(html))

    elif env == 'Streamlit':
        import streamlit.components.v1 as components
        components.html(html, height=1000, scrolling=True)
    elif env == 'Widgets':
        import ipywidgets as wgt

    else:
        print("The environment is not supported yet, Please use the options given")
