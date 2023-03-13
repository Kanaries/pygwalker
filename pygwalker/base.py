import os, sys, json
import typing as tp
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
    
import IPython
from IPython.display import display, Javascript, HTML, IFrame

HERE = os.path.dirname(os.path.abspath(__file__))

gwalker_js = None

global_gid = 0
