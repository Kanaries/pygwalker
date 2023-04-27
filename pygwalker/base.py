import os, sys, json
import typing as tp
import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
BYTE_LIMIT = 1 << 24
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
    
import IPython
from IPython.display import display, Javascript, HTML, IFrame
from .__version__ import __version__

import random, string

def rand_str(n: int = 8, options: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.sample(options, n))

__hash__ = rand_str()

HERE = os.path.dirname(os.path.abspath(__file__))

gwalker_js = None

global_gid = 0
