from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from pygwalker.utils.randoms import rand_str


def render_explore_modal_button(html: str, left: int, size: int):
    """
    render explore modal button
    """
    temp_id = rand_str(8)
    st.markdown(f"""
    <style>.element-container:has(#button-after-{temp_id}) + div button {{
        position: relative;
        top: 20px;
        left: {left}px;
        z-index: 999;
        height: {size}px;
        width: {size}px;
        border-radius: 50%;
        padding: 0px;
        min-height: 0px;
    }}
    .element-container:has(#button-after-{temp_id}) + div {{
        height: 0;
    }}
    </style>""", unsafe_allow_html=True)
    st.markdown(f'<span id="button-after-{temp_id}"></span>', unsafe_allow_html=True)
    st.button(
        '...',
        key=temp_id,
        on_click=lambda: render_modal(html)
    )


def render_modal(html: str, key: Optional[str] = None):
    """
    show a modal dialog.
    css style and hack way reference: https://github.com/teamtv/streamlit_modal
    """
    if key is None:
        key = "modal_" + rand_str()

    padding = 5

    modal_style = f"""
        <style>
        div[data-modal-container='true'][key='{key}'] {{
            position: fixed;
            width: 100vw !important;
            left: 0;
            z-index: 1001;
            max-height: 86vh;
            overflow-y: auto;
        }}

        div[data-modal-container='true'][key='{key}'] > div:first-child {{
            margin: auto;
        }}

        div[data-modal-container='true'][key='{key}']::before {{
                position: fixed;
                content: ' ';
                left: 0;
                right: 0;
                top: 0;
                bottom: 0;
                z-index: 1000;
                background-color: rgba(0, 0, 0, 0.5);
        }}
        div[data-modal-container='true'][key='{key}'] > div:first-child {{
            max-width: "unset";
        }}

        div[data-modal-container='true'][key='{key}'] > div:first-child > div:first-child {{
            width: unset !important;
            background-color: #fff;
            padding: {padding}px;
            margin-top: {2*padding}px;
            margin-left: -{padding}px;
            margin-right: -{padding}px;
            margin-bottom: -{2*padding}px;
            z-index: 1001;
            border-radius: 5px;
        }}
        div[data-modal-container='true'][key='{key}'] > div > div:nth-child(2)  {{
            z-index: 1003;
            position: absolute;
        }}
        div[data-modal-container='true'][key='{key}'] > div > div:nth-child(2) > div {{
            text-align: right;
            padding-right: {padding}px;
            max-width: "unset";
        }}

        div[data-modal-container='true'][key='{key}'] > div > div:nth-child(2) > div > button {{
            right: 0;
            margin-top: {2*padding + 14}px;
        }}
        </style>
     """

    close_button_code = f"""
        <style>
        #modal-cancel-{key} {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: none;
            outline: none;
        }}
        </style>
        <div style="display: flex; justify-content: right;">
            <svg id="modal-cancel-{key}" width="20" height="20" viewBox="0 0 20 20">
                <line x1="2" y1="2" x2="18" y2="18" stroke="#ccc" stroke-width="2"/>
                <line x1="2" y1="18" x2="18" y2="2" stroke="#ccc" stroke-width="2"/>
            </svg>
        </div>
        <script>
            var button = document.getElementById("modal-cancel-{key}");
            const buttonCallback = () => {{
                const iframes = parent.document.body.getElementsByTagName('iframe');
                for(const iframe of iframes) {{
                    if (iframe.srcdoc.startsWith("<!-- STREAMLIT-MODAL-IFRAME-{key}")) {{
                        container = iframe.parentNode.previousSibling;
                        if (container.className === "resize-triggers") {{
                            container = container.previousSibling;
                        }}
                        container.style="display: none";
                    }}
                }}
            }}
            button.addEventListener('click', buttonCallback);
        </script>
    """

    # rand_str() is used to prevent the browser from caching the iframe
    add_style_code = f"""<!-- STREAMLIT-MODAL-IFRAME-{key} -->
        <script>
        // {rand_str()}
        const iframes = parent.document.body.getElementsByTagName('iframe');
        let container
        for(const iframe of iframes) {{
            if (iframe.srcdoc.startsWith("<!-- STREAMLIT-MODAL-IFRAME-{key}")) {{
                container = iframe.parentNode.previousSibling;
                if (container.className === "resize-triggers") {{
                    container = container.previousSibling;
                }}
                container.setAttribute('data-modal-container', 'true');
                container.setAttribute('key', '{key}');
                container.style="display: unset";
            }}
        }}
        </script>
    """

    # init modal style
    st.markdown(modal_style, unsafe_allow_html=True)

    with st.container():
        container = st.container()
        container._html(close_button_code, height=36)
        container._html(html, height=920)

    # position node and add style to container
    components.html(add_style_code, height=0, width=0)
