import os, sys, json
import typing as tp
BYTE_LIMIT = 1 << 24
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
    
import IPython
from IPython.display import display, Javascript, HTML, IFrame
from .__version__ import __version__

import random, string
__hash__ = ''.join(random.sample(string.ascii_letters + string.digits, 8))

HERE = os.path.dirname(os.path.abspath(__file__))

gwalker_js = None

global_gid = 0
