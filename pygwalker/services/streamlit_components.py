from typing import Dict, Any
import os

from streamlit.components.v1.components import CustomComponent
import streamlit.components.v1 as components

from pygwalker._constants import ROOT_DIR

_build_dir = os.path.join(ROOT_DIR, "templates")
_component_func = components.declare_component("pygwalker_component", path=_build_dir)


def pygwalker_component(props: Dict[str, Any], key: str) -> CustomComponent:
    return _component_func(
        key=key,
        **props,
    )
