from typing import Dict, Any
import os

import streamlit as st
import streamlit.components.v1 as components

from pygwalker.communications.base import BaseCommunication
from pygwalker._constants import ROOT_DIR

_build_dir = os.path.join(ROOT_DIR, "templates")
_component_func = components.declare_component("pygwalker_component", path=_build_dir)


def pygwalker_component(props: Dict[str, Any], comm: BaseCommunication, key: str):
    component_value = _component_func(
        key=key,
        **props,
        comm_callback_msg=st.session_state.get(key, {"request": None, "response": None})
    )

    if not component_value:
        return

    if component_value["request"]:
        result = [
            {
                "rid": action_info["rid"],
                "data": comm._receive_msg(action_info["action"], action_info["data"])
            }
            for action_info in component_value["request"]
        ]
        st.session_state[key]["response"] = result
        st.session_state[key]["request"] = None
        st.rerun()
